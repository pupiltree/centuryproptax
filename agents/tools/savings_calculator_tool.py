"""
Savings Calculator Tool for Texas Property Tax System

Calculates potential tax savings from appeals, exemptions, and other strategies.
Provides detailed before/after scenarios with accurate estimates.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from datetime import datetime, timedelta

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from mock_data.tax_rates import (
    calculate_total_tax_rate,
    calculate_exemption_value,
    estimate_appeal_outcome,
    get_county_tax_info,
    get_exemption_info,
    COUNTY_TAX_RATES,
    EXEMPTION_CRITERIA
)

logger = structlog.get_logger()

class SavingsCalculationInput(BaseModel):
    """Input schema for savings calculation"""
    property_value: int = Field(description="Current assessed property value")
    county_code: str = Field(description="County code (e.g., 'harris', 'dallas')")
    city: Optional[str] = Field(default=None, description="City name for municipal rates")
    school_district: Optional[str] = Field(default=None, description="School district for accurate rates")
    property_type: str = Field(default="residential", description="Property type: residential, commercial, industrial, agricultural")
    current_exemptions: Dict[str, bool] = Field(
        default_factory=dict,
        description="Currently applied exemptions"
    )
    potential_exemptions: Dict[str, bool] = Field(
        default_factory=dict,
        description="Exemptions to evaluate for savings"
    )
    appeal_scenario: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Appeal scenario with evidence strength and target reduction"
    )
    calculation_type: str = Field(
        default="comprehensive",
        description="Type of calculation: exemption_only, appeal_only, comprehensive"
    )

class SavingsCalculationResponse(BaseModel):
    """Response schema for savings calculation"""
    success: bool = Field(description="Whether calculation was successful")
    current_scenario: Dict[str, Any] = Field(description="Current tax situation")
    optimized_scenario: Dict[str, Any] = Field(description="Optimized tax situation with recommended changes")
    savings_summary: Dict[str, Any] = Field(description="Summary of potential savings")
    recommendations: List[Dict[str, str]] = Field(description="Specific recommendations for savings")
    scenarios_compared: List[Dict[str, Any]] = Field(description="Different scenarios compared")

def calculate_annual_tax(
    assessed_value: int,
    exemption_value: int,
    tax_rate: float
) -> Dict[str, Any]:
    """Calculate annual tax with exemptions applied"""
    taxable_value = max(0, assessed_value - exemption_value)
    annual_tax = int(taxable_value * tax_rate)

    return {
        "assessed_value": assessed_value,
        "exemption_value": exemption_value,
        "taxable_value": taxable_value,
        "tax_rate": tax_rate,
        "annual_tax": annual_tax
    }

def analyze_exemption_opportunities(
    property_type: str,
    current_exemptions: Dict[str, bool],
    property_characteristics: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Analyze potential exemption opportunities"""
    opportunities = []

    # Homestead exemption (most common)
    if not current_exemptions.get("homestead") and property_type == "residential":
        homestead_info = get_exemption_info("homestead")
        opportunities.append({
            "exemption_type": "homestead",
            "name": homestead_info["name"],
            "value": homestead_info["value"],
            "requirements": homestead_info["requirements"],
            "priority": "high",
            "estimated_qualification": "very_likely" if property_type == "residential" else "unlikely"
        })

    # Senior citizen exemption
    if not current_exemptions.get("senior") and current_exemptions.get("homestead"):
        senior_info = get_exemption_info("senior_citizen")
        opportunities.append({
            "exemption_type": "senior_citizen",
            "name": senior_info["name"],
            "value": senior_info["value"],
            "requirements": senior_info["requirements"],
            "priority": "medium",
            "estimated_qualification": "depends_on_age",
            "additional_benefit": "Tax ceiling at age 65 amount"
        })

    # Disability exemption
    if not current_exemptions.get("disability") and current_exemptions.get("homestead"):
        disability_info = get_exemption_info("disability")
        opportunities.append({
            "exemption_type": "disability",
            "name": disability_info["name"],
            "value": disability_info["value"],
            "requirements": disability_info["requirements"],
            "priority": "medium",
            "estimated_qualification": "depends_on_disability_status"
        })

    # Veteran exemptions
    if not current_exemptions.get("veteran"):
        veteran_info = get_exemption_info("disabled_veteran")
        opportunities.append({
            "exemption_type": "disabled_veteran",
            "name": veteran_info["name"],
            "values": veteran_info["values"],
            "requirements": veteran_info["requirements"],
            "priority": "high",
            "estimated_qualification": "depends_on_service_and_disability"
        })

    # Agricultural exemption
    if (property_type == "agricultural" and
        not current_exemptions.get("agricultural") and
        property_characteristics and
        property_characteristics.get("total_acres", 0) >= 5):

        ag_info = get_exemption_info("agricultural")
        opportunities.append({
            "exemption_type": "agricultural",
            "name": ag_info["name"],
            "description": ag_info["description_detailed"],
            "requirements": ag_info["requirements"],
            "priority": "very_high",
            "estimated_qualification": "likely",
            "typical_savings_percent": ag_info["typical_savings"]
        })

    return opportunities

def generate_appeal_scenarios(
    current_value: int,
    property_type: str,
    county_code: str
) -> List[Dict[str, Any]]:
    """Generate different appeal scenarios with varying evidence strength"""
    scenarios = []

    evidence_levels = [
        {"name": "Conservative Appeal", "strength": "moderate", "description": "Standard comparable sales analysis"},
        {"name": "Strong Appeal", "strength": "strong", "description": "Multiple comparable sales plus property issues"},
        {"name": "Aggressive Appeal", "strength": "very_strong", "description": "Comprehensive evidence package with expert testimony"}
    ]

    for scenario in evidence_levels:
        appeal_outcome = estimate_appeal_outcome(
            current_value,
            property_type,
            county_code,
            scenario["strength"]
        )

        if "error" not in appeal_outcome:
            scenarios.append({
                "scenario_name": scenario["name"],
                "evidence_strength": scenario["strength"],
                "description": scenario["description"],
                "success_probability": appeal_outcome["success_probability"],
                "potential_reduction_percent": appeal_outcome["estimated_reduction_percent"],
                "potential_new_value": appeal_outcome["potential_new_value"],
                "value_reduction": appeal_outcome["potential_value_reduction"]
            })

    return scenarios

@tool("savings_calculator_tool", return_direct=False)
async def savings_calculator_tool(
    property_value: int,
    county_code: str,
    city: Optional[str] = None,
    school_district: Optional[str] = None,
    property_type: str = "residential",
    current_exemptions: Optional[Dict[str, bool]] = None,
    potential_exemptions: Optional[Dict[str, bool]] = None,
    appeal_scenario: Optional[Dict[str, Any]] = None,
    calculation_type: str = "comprehensive"
) -> Dict[str, Any]:
    """
    Calculate potential property tax savings from appeals, exemptions, and optimization strategies.

    Provides detailed before/after scenarios with accurate Texas tax calculations
    including county, school district, municipal, and other entity rates.

    Args:
        property_value: Current assessed property value
        county_code: County code (harris, dallas, tarrant, travis, bexar, collin)
        city: City name for municipal tax rates
        school_district: School district for accurate rate calculation
        property_type: Property type (residential, commercial, industrial, agricultural)
        current_exemptions: Currently applied exemptions (homestead, senior, disability, veteran)
        potential_exemptions: Exemptions to evaluate
        appeal_scenario: Appeal details with evidence strength
        calculation_type: Type of analysis (exemption_only, appeal_only, comprehensive)

    Returns:
        Comprehensive savings analysis with recommendations and scenarios
    """
    try:
        logger.info("💰 Processing savings calculation request",
                   property_value=property_value, county=county_code,
                   property_type=property_type, calculation_type=calculation_type)

        # Validate inputs
        if property_value <= 0:
            return {
                "success": False,
                "error": "Property value must be greater than 0",
                "suggestions": ["Please provide a valid property assessment value"]
            }

        county_info = get_county_tax_info(county_code)
        if not county_info:
            return {
                "success": False,
                "error": f"County '{county_code}' not supported",
                "suggestions": [f"Supported counties: {', '.join(COUNTY_TAX_RATES.keys())}"]
            }

        # Set defaults
        current_exemptions = current_exemptions or {}
        potential_exemptions = potential_exemptions or {}

        # Calculate current tax situation
        current_tax_rate_info = calculate_total_tax_rate(county_code, city, school_district)
        current_tax_rate = current_tax_rate_info["total_rate"]
        current_exemption_value = calculate_exemption_value(current_exemptions, county_code)

        current_scenario = calculate_annual_tax(
            property_value,
            current_exemption_value,
            current_tax_rate
        )
        current_scenario["rate_breakdown"] = current_tax_rate_info["breakdown"]
        current_scenario["exemptions_applied"] = current_exemptions

        # Initialize optimization scenario
        best_scenario = current_scenario.copy()
        optimization_steps = []

        # Exemption optimization
        if calculation_type in ["exemption_only", "comprehensive"]:
            # Analyze exemption opportunities
            exemption_opportunities = analyze_exemption_opportunities(
                property_type,
                current_exemptions
            )

            # Calculate with potential exemptions
            combined_exemptions = {**current_exemptions, **potential_exemptions}
            potential_exemption_value = calculate_exemption_value(combined_exemptions, county_code)

            if potential_exemption_value > current_exemption_value:
                exemption_scenario = calculate_annual_tax(
                    property_value,
                    potential_exemption_value,
                    current_tax_rate
                )
                exemption_scenario["rate_breakdown"] = current_tax_rate_info["breakdown"]
                exemption_scenario["exemptions_applied"] = combined_exemptions

                exemption_savings = current_scenario["annual_tax"] - exemption_scenario["annual_tax"]

                if exemption_savings > 0:
                    best_scenario = exemption_scenario
                    optimization_steps.append({
                        "step": "exemption_optimization",
                        "description": "Apply additional exemptions",
                        "annual_savings": exemption_savings,
                        "new_annual_tax": exemption_scenario["annual_tax"]
                    })

        # Appeal optimization
        appeal_scenarios = []
        if calculation_type in ["appeal_only", "comprehensive"]:
            appeal_scenarios = generate_appeal_scenarios(property_value, property_type, county_code)

            # Use custom appeal scenario if provided
            if appeal_scenario:
                custom_appeal = estimate_appeal_outcome(
                    property_value,
                    property_type,
                    county_code,
                    appeal_scenario.get("evidence_strength", "moderate")
                )

                if "error" not in custom_appeal:
                    # Calculate tax with appealed value
                    appealed_value = custom_appeal["potential_new_value"]
                    appeal_tax_scenario = calculate_annual_tax(
                        appealed_value,
                        best_scenario["exemption_value"],  # Keep best exemptions
                        current_tax_rate
                    )

                    appeal_savings = best_scenario["annual_tax"] - appeal_tax_scenario["annual_tax"]

                    if appeal_savings > 0:
                        best_scenario = appeal_tax_scenario
                        best_scenario["appealed_value"] = appealed_value
                        best_scenario["appeal_details"] = custom_appeal

                        optimization_steps.append({
                            "step": "appeal_optimization",
                            "description": f"Property tax appeal with {appeal_scenario.get('evidence_strength', 'moderate')} evidence",
                            "annual_savings": appeal_savings,
                            "new_annual_tax": appeal_tax_scenario["annual_tax"],
                            "success_probability": custom_appeal["success_probability"]
                        })

        # Calculate total savings
        total_annual_savings = current_scenario["annual_tax"] - best_scenario["annual_tax"]
        total_5_year_savings = total_annual_savings * 5
        savings_percentage = (total_annual_savings / current_scenario["annual_tax"]) * 100 if current_scenario["annual_tax"] > 0 else 0

        # Generate recommendations
        recommendations = []

        if not current_exemptions.get("homestead") and property_type == "residential":
            recommendations.append({
                "type": "exemption",
                "priority": "high",
                "title": "Apply for Homestead Exemption",
                "description": "Save $100,000 in taxable value - must be primary residence",
                "estimated_annual_savings": int(100000 * current_tax_rate),
                "action": "File application before April 30"
            })

        if total_annual_savings > 500:
            if optimization_steps:
                for step in optimization_steps:
                    if step["step"] == "exemption_optimization":
                        recommendations.append({
                            "type": "exemption",
                            "priority": "high",
                            "title": "Maximize Available Exemptions",
                            "description": "Apply for all qualifying exemptions",
                            "estimated_annual_savings": step["annual_savings"],
                            "action": "Contact county appraisal district"
                        })
                    elif step["step"] == "appeal_optimization":
                        recommendations.append({
                            "type": "appeal",
                            "priority": "medium",
                            "title": "File Property Tax Appeal",
                            "description": f"Challenge assessment with {step.get('success_probability', 'moderate')} success probability",
                            "estimated_annual_savings": step["annual_savings"],
                            "action": "File protest before May 15 (or 30 days after notice)"
                        })

        # Create scenario comparisons
        scenarios_compared = [
            {
                "name": "Current Situation",
                "assessed_value": current_scenario["assessed_value"],
                "exemption_value": current_scenario["exemption_value"],
                "taxable_value": current_scenario["taxable_value"],
                "annual_tax": current_scenario["annual_tax"],
                "exemptions": current_exemptions
            },
            {
                "name": "Optimized Situation",
                "assessed_value": best_scenario["assessed_value"],
                "exemption_value": best_scenario["exemption_value"],
                "taxable_value": best_scenario["taxable_value"],
                "annual_tax": best_scenario["annual_tax"],
                "exemptions": best_scenario.get("exemptions_applied", current_exemptions),
                "appeal_applied": "appealed_value" in best_scenario
            }
        ]

        return {
            "success": True,
            "current_scenario": current_scenario,
            "optimized_scenario": best_scenario,
            "savings_summary": {
                "annual_savings": total_annual_savings,
                "five_year_savings": total_5_year_savings,
                "savings_percentage": round(savings_percentage, 2),
                "optimization_steps": optimization_steps
            },
            "recommendations": recommendations,
            "scenarios_compared": scenarios_compared,
            "appeal_scenarios": appeal_scenarios if appeal_scenarios else [],
            "exemption_opportunities": exemption_opportunities if calculation_type in ["exemption_only", "comprehensive"] else [],
            "calculation_details": {
                "county": county_info["county_name"],
                "tax_rate_breakdown": current_tax_rate_info["breakdown"],
                "total_tax_rate": current_tax_rate,
                "property_type": property_type,
                "calculation_date": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error("❌ Savings calculation failed",
                    error=str(e), property_value=property_value, county=county_code)

        return {
            "success": False,
            "error": f"Calculation failed: {str(e)}",
            "suggestions": [
                "Verify property value is a positive number",
                "Check county code is valid (harris, dallas, tarrant, travis, bexar, collin)",
                "Ensure property type is valid (residential, commercial, industrial, agricultural)",
                "Contact support if the problem persists"
            ]
        }

# Additional utility functions

async def calculate_multi_year_projections(
    base_calculation: Dict[str, Any],
    years: int = 5,
    annual_appreciation: float = 0.05
) -> List[Dict[str, Any]]:
    """Calculate multi-year savings projections with property value appreciation"""
    projections = []
    current_value = base_calculation["current_scenario"]["assessed_value"]

    for year in range(1, years + 1):
        projected_value = int(current_value * (1 + annual_appreciation) ** year)

        # Recalculate with projected value
        year_calculation = await savings_calculator_tool(
            property_value=projected_value,
            county_code=base_calculation["calculation_details"]["county"].lower().replace(" county", ""),
            calculation_type="comprehensive"
        )

        projections.append({
            "year": year,
            "projected_value": projected_value,
            "projected_savings": year_calculation.get("savings_summary", {}).get("annual_savings", 0)
        })

    return projections

def compare_county_rates(property_value: int, counties: List[str]) -> Dict[str, Any]:
    """Compare tax burden across different Texas counties"""
    comparisons = {}

    for county in counties:
        if county in COUNTY_TAX_RATES:
            # Use default homestead exemption for comparison
            exemptions = {"homestead": True}
            rate_info = calculate_total_tax_rate(county, None, None)
            exemption_value = calculate_exemption_value(exemptions, county)

            tax_calc = calculate_annual_tax(
                property_value,
                exemption_value,
                rate_info["total_rate"]
            )

            comparisons[county] = {
                "county_name": COUNTY_TAX_RATES[county]["county_name"],
                "total_rate": rate_info["total_rate"],
                "annual_tax": tax_calc["annual_tax"],
                "effective_rate": round((tax_calc["annual_tax"] / property_value) * 100, 3)
            }

    return comparisons