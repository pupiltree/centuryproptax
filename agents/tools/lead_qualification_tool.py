"""
Lead Qualification Tool for Texas Property Tax System

Scores potential customers based on property value, assessment increases,
appeal likelihood, and potential savings to prioritize sales efforts.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from mock_data.assessment_patterns import (
    calculate_assessment_increase_percentage,
    get_increase_category,
    get_value_range_category,
    estimate_appeal_success_probability,
    calculate_estimated_savings,
    determine_market_segment,
    QUALIFICATION_CRITERIA,
    LEAD_QUALITY_INDICATORS,
    MARKET_SEGMENTS
)
from mock_data.tax_rates import (
    calculate_total_tax_rate,
    COUNTY_TAX_RATES
)

logger = structlog.get_logger()

class LeadQualificationInput(BaseModel):
    """Input schema for lead qualification"""
    property_value: int = Field(description="Current assessed property value")
    previous_value: Optional[int] = Field(default=None, description="Previous year assessed value")
    county_code: str = Field(description="County code for the property")
    property_type: str = Field(default="residential", description="Type of property")
    city: Optional[str] = Field(default=None, description="City for tax rate calculation")
    school_district: Optional[str] = Field(default=None, description="School district")
    appeal_history: Optional[str] = Field(
        default="never_appealed",
        description="Appeal history: never_appealed, successful_appeal, unsuccessful_appeal, multiple_appeals"
    )
    customer_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional customer information"
    )
    lead_source: Optional[str] = Field(default="unknown", description="Source of the lead")

class LeadQualificationResponse(BaseModel):
    """Response schema for lead qualification"""
    success: bool = Field(description="Whether qualification was successful")
    qualification_score: int = Field(description="Overall qualification score (0-100)")
    quality_tier: str = Field(description="Lead quality tier")
    estimated_savings: Dict[str, Any] = Field(description="Potential tax savings")
    appeal_analysis: Dict[str, Any] = Field(description="Appeal success analysis")
    recommendations: Dict[str, Any] = Field(description="Sales and approach recommendations")
    priority_level: str = Field(description="Contact priority level")
    market_segment: Optional[str] = Field(description="Market segment classification")

def calculate_qualification_score(
    property_value: int,
    assessment_increase: float,
    property_type: str,
    county_code: str,
    appeal_history: str
) -> Dict[str, Any]:
    """Calculate comprehensive qualification score"""

    # Property Value Score (0-10)
    value_category = get_value_range_category(property_value, property_type)
    value_score = QUALIFICATION_CRITERIA["property_value_score"].get(value_category, 5)

    # Assessment Increase Score (0-10)
    increase_category = get_increase_category(assessment_increase)
    increase_score = QUALIFICATION_CRITERIA["assessment_increase_score"].get(increase_category, 5)

    # Property Type Score (0-10)
    type_score = QUALIFICATION_CRITERIA["property_type_score"].get(property_type.lower(), 5)

    # County Score (0-10)
    county_score = QUALIFICATION_CRITERIA["county_score"].get(county_code.lower(), 5)

    # Appeal History Score (0-10)
    history_score = QUALIFICATION_CRITERIA["appeal_history_score"].get(appeal_history.lower(), 5)

    # Calculate weighted total (out of 100)
    # Weights: Value (25%), Increase (30%), Type (15%), County (15%), History (15%)
    total_score = (
        value_score * 0.25 +
        increase_score * 0.30 +
        type_score * 0.15 +
        county_score * 0.15 +
        history_score * 0.15
    ) * 10

    return {
        "total_score": round(total_score),
        "component_scores": {
            "property_value": value_score,
            "assessment_increase": increase_score,
            "property_type": type_score,
            "county": county_score,
            "appeal_history": history_score
        },
        "score_breakdown": {
            "value_category": value_category,
            "increase_category": increase_category,
            "property_type": property_type,
            "county": county_code,
            "appeal_history": appeal_history
        }
    }

def determine_quality_tier(qualification_score: int) -> Dict[str, Any]:
    """Determine lead quality tier based on score"""
    for tier, criteria in LEAD_QUALITY_INDICATORS.items():
        score_range = criteria["score_range"]
        if score_range[0] <= qualification_score <= score_range[1]:
            return {
                "tier": tier,
                "score_range": score_range,
                "characteristics": criteria["characteristics"],
                "estimated_savings_range": criteria["estimated_savings"],
                "success_probability": criteria["success_probability"],
                "priority": criteria["priority"]
            }

    # Default to very_low if no match
    return LEAD_QUALITY_INDICATORS["very_low"].copy()

def generate_sales_recommendations(
    quality_tier: str,
    market_segment: Optional[str],
    estimated_savings: Dict[str, Any],
    property_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate sales approach recommendations"""

    tier_info = LEAD_QUALITY_INDICATORS.get(quality_tier, {})
    segment_info = MARKET_SEGMENTS.get(market_segment, {}) if market_segment else {}

    recommendations = {
        "contact_priority": tier_info.get("priority", "contact_when_available"),
        "approach_strategy": "",
        "key_talking_points": [],
        "pricing_strategy": "",
        "follow_up_schedule": "",
        "success_factors": []
    }

    # Approach strategy based on tier
    if quality_tier == "very_high":
        recommendations["approach_strategy"] = "Immediate high-touch approach with senior team member"
        recommendations["pricing_strategy"] = "Premium pricing justified by high savings potential"
        recommendations["follow_up_schedule"] = "Daily follow-up until contact made, then aggressive pursuit"

    elif quality_tier == "high":
        recommendations["approach_strategy"] = "Personal phone call within 24 hours"
        recommendations["pricing_strategy"] = "Standard pricing with savings guarantee"
        recommendations["follow_up_schedule"] = "Contact within 24h, follow up every 2-3 days"

    elif quality_tier == "medium":
        recommendations["approach_strategy"] = "Email first, then phone call if responsive"
        recommendations["pricing_strategy"] = "Competitive pricing with payment plans if needed"
        recommendations["follow_up_schedule"] = "Email within 2 days, call within week, weekly follow-up"

    elif quality_tier == "low":
        recommendations["approach_strategy"] = "Automated email campaign with periodic check-ins"
        recommendations["pricing_strategy"] = "Discounted pricing or group processing"
        recommendations["follow_up_schedule"] = "Monthly automated follow-up"

    else:  # very_low
        recommendations["approach_strategy"] = "No active pursuit - add to newsletter list only"
        recommendations["pricing_strategy"] = "Not recommended to pursue"
        recommendations["follow_up_schedule"] = "No follow-up recommended"

    # Key talking points based on savings potential
    expected_savings = estimated_savings.get("expected_annual_savings", 0)
    if expected_savings >= 5000:
        recommendations["key_talking_points"].extend([
            f"Potential to save ${expected_savings:,} annually",
            "High-value property qualifies for significant tax reduction",
            "Professional appeal process with proven success rate"
        ])
    elif expected_savings >= 2000:
        recommendations["key_talking_points"].extend([
            f"Save approximately ${expected_savings:,} per year",
            "Assessment increase justifies professional appeal",
            "Low-risk investment with high return potential"
        ])
    else:
        recommendations["key_talking_points"].extend([
            "Modest savings potential but worth investigating",
            "Professional review at minimal cost",
            "Part of ongoing tax optimization strategy"
        ])

    # Market segment specific adjustments
    if segment_info:
        customer_profile = segment_info.get("customer_profile", {})
        if customer_profile.get("preferred_contact") == "phone":
            recommendations["approach_strategy"] += " - Prefer phone contact"
        elif customer_profile.get("preferred_contact") == "email":
            recommendations["approach_strategy"] += " - Email preferred initially"

        if customer_profile.get("decision_speed") == "fast":
            recommendations["success_factors"].append("Quick decision maker - strike while interest is high")
        elif customer_profile.get("decision_speed") == "slow":
            recommendations["success_factors"].append("Deliberate decision maker - provide comprehensive information")

    return recommendations

@tool("lead_qualification_tool", return_direct=False)
async def lead_qualification_tool(
    property_value: int,
    county_code: str,
    previous_value: Optional[int] = None,
    property_type: str = "residential",
    city: Optional[str] = None,
    school_district: Optional[str] = None,
    appeal_history: str = "never_appealed",
    customer_info: Optional[Dict[str, Any]] = None,
    lead_source: str = "unknown"
) -> Dict[str, Any]:
    """
    Qualify property tax appeal leads based on property characteristics and potential savings.

    Analyzes property value, assessment increases, county patterns, and appeal history
    to generate qualification scores and sales recommendations.

    Args:
        property_value: Current assessed property value
        county_code: County code (harris, dallas, tarrant, travis, bexar, collin)
        previous_value: Previous year assessed value for increase calculation
        property_type: Property type (residential, commercial, industrial, agricultural)
        city: City for accurate tax rate calculation
        school_district: School district for rate calculation
        appeal_history: Appeal history (never_appealed, successful_appeal, unsuccessful_appeal, multiple_appeals)
        customer_info: Additional customer information
        lead_source: Source of the lead

    Returns:
        Comprehensive lead qualification with scores, recommendations, and priority level
    """
    try:
        logger.info("🎯 Processing lead qualification request",
                   property_value=property_value, county=county_code,
                   property_type=property_type)

        # Validate inputs
        if property_value <= 0:
            return {
                "success": False,
                "error": "Property value must be greater than 0",
                "suggestions": ["Please provide a valid property assessment value"]
            }

        if county_code.lower() not in COUNTY_TAX_RATES:
            return {
                "success": False,
                "error": f"County '{county_code}' not supported",
                "suggestions": [f"Supported counties: {', '.join(COUNTY_TAX_RATES.keys())}"]
            }

        # Calculate assessment increase
        if previous_value and previous_value > 0:
            assessment_increase = calculate_assessment_increase_percentage(property_value, previous_value)
        else:
            # Estimate based on county averages if no previous value provided
            from mock_data.assessment_patterns import ASSESSMENT_INCREASE_PATTERNS
            county_patterns = ASSESSMENT_INCREASE_PATTERNS.get(county_code.lower(), {})
            property_patterns = county_patterns.get(property_type.lower(), {})
            avg_increase = property_patterns.get("avg_annual_increase", 0.05)
            assessment_increase = avg_increase * 100  # Convert to percentage

        # Calculate qualification score
        score_info = calculate_qualification_score(
            property_value,
            assessment_increase,
            property_type,
            county_code,
            appeal_history
        )

        qualification_score = score_info["total_score"]

        # Determine quality tier
        quality_tier_info = determine_quality_tier(qualification_score)
        quality_tier = quality_tier_info["tier"]

        # Calculate tax rate for savings estimation
        tax_rate_info = calculate_total_tax_rate(county_code, city, school_district)
        tax_rate = tax_rate_info["total_rate"]

        # Estimate appeal success and savings
        appeal_analysis = estimate_appeal_success_probability(
            county_code,
            property_type,
            property_value,
            assessment_increase
        )

        estimated_savings = calculate_estimated_savings(
            property_value,
            tax_rate,
            appeal_analysis["estimated_reduction"],
            appeal_analysis["success_probability"]
        )

        # Determine market segment
        market_segment = determine_market_segment(property_value, property_type)

        # Generate sales recommendations
        property_info = {
            "value": property_value,
            "type": property_type,
            "county": county_code,
            "assessment_increase": assessment_increase
        }

        sales_recommendations = generate_sales_recommendations(
            quality_tier,
            market_segment,
            estimated_savings,
            property_info
        )

        # Calculate ROI for customer
        estimated_annual_savings = estimated_savings["expected_annual_savings"]
        estimated_fee = max(500, min(estimated_annual_savings * 0.30, 5000))  # 30% of savings, capped
        roi_percentage = ((estimated_annual_savings - estimated_fee) / estimated_fee * 100) if estimated_fee > 0 else 0

        # Compile final response
        return {
            "success": True,
            "qualification_score": qualification_score,
            "quality_tier": quality_tier,
            "estimated_savings": {
                **estimated_savings,
                "estimated_service_fee": int(estimated_fee),
                "net_first_year_savings": estimated_annual_savings - int(estimated_fee),
                "roi_percentage": round(roi_percentage, 1)
            },
            "appeal_analysis": appeal_analysis,
            "recommendations": sales_recommendations,
            "priority_level": quality_tier_info["priority"],
            "market_segment": market_segment,
            "property_analysis": {
                "current_value": property_value,
                "previous_value": previous_value,
                "assessment_increase_percent": round(assessment_increase, 2),
                "increase_category": score_info["score_breakdown"]["increase_category"],
                "value_category": score_info["score_breakdown"]["value_category"],
                "appeal_history": appeal_history,
                "county": county_code,
                "property_type": property_type
            },
            "score_breakdown": score_info,
            "quality_indicators": quality_tier_info,
            "market_segment_info": MARKET_SEGMENTS.get(market_segment, {}) if market_segment else None,
            "lead_metadata": {
                "lead_source": lead_source,
                "qualification_date": datetime.now().isoformat(),
                "customer_info": customer_info or {},
                "next_action": sales_recommendations["contact_priority"]
            }
        }

    except Exception as e:
        logger.error("❌ Lead qualification failed",
                    error=str(e), property_value=property_value, county=county_code)

        return {
            "success": False,
            "error": f"Lead qualification failed: {str(e)}",
            "suggestions": [
                "Verify property value is a positive number",
                "Check county code is valid (harris, dallas, tarrant, travis, bexar, collin)",
                "Ensure property type is valid (residential, commercial, industrial, agricultural)",
                "Verify appeal history is valid (never_appealed, successful_appeal, unsuccessful_appeal, multiple_appeals)",
                "Contact support if the problem persists"
            ]
        }

# Additional utility functions

async def qualify_multiple_leads(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Qualify multiple leads in batch"""
    results = []

    for lead in leads:
        result = await lead_qualification_tool(**lead)
        results.append(result)

    # Sort by qualification score (highest first)
    results.sort(key=lambda x: x.get("qualification_score", 0), reverse=True)

    return results

def generate_lead_report(qualified_leads: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary report of qualified leads"""
    if not qualified_leads:
        return {"error": "No leads provided"}

    total_leads = len(qualified_leads)
    quality_distribution = {}
    total_potential_savings = 0
    high_priority_count = 0

    for lead in qualified_leads:
        if not lead.get("success"):
            continue

        # Count quality tiers
        tier = lead.get("quality_tier", "unknown")
        quality_distribution[tier] = quality_distribution.get(tier, 0) + 1

        # Sum potential savings
        savings = lead.get("estimated_savings", {}).get("expected_annual_savings", 0)
        total_potential_savings += savings

        # Count high priority leads
        if lead.get("priority_level") in ["immediate_contact", "contact_within_24h"]:
            high_priority_count += 1

    return {
        "total_leads": total_leads,
        "quality_distribution": quality_distribution,
        "high_priority_count": high_priority_count,
        "total_potential_annual_savings": total_potential_savings,
        "average_qualification_score": sum(
            lead.get("qualification_score", 0) for lead in qualified_leads if lead.get("success")
        ) / max(1, len([l for l in qualified_leads if l.get("success")])),
        "top_leads": sorted(
            [l for l in qualified_leads if l.get("success")],
            key=lambda x: x.get("qualification_score", 0),
            reverse=True
        )[:5]  # Top 5 leads
    }

def filter_leads_by_criteria(
    qualified_leads: List[Dict[str, Any]],
    min_score: int = 0,
    quality_tiers: Optional[List[str]] = None,
    min_savings: int = 0,
    counties: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Filter qualified leads by specific criteria"""
    filtered_leads = []

    for lead in qualified_leads:
        if not lead.get("success"):
            continue

        # Score filter
        if lead.get("qualification_score", 0) < min_score:
            continue

        # Quality tier filter
        if quality_tiers and lead.get("quality_tier") not in quality_tiers:
            continue

        # Savings filter
        if lead.get("estimated_savings", {}).get("expected_annual_savings", 0) < min_savings:
            continue

        # County filter
        if counties and lead.get("property_analysis", {}).get("county") not in counties:
            continue

        filtered_leads.append(lead)

    return filtered_leads

def get_lead_recommendations_summary(quality_tier: str) -> Dict[str, Any]:
    """Get summary of recommendations for a quality tier"""
    tier_info = LEAD_QUALITY_INDICATORS.get(quality_tier, {})

    return {
        "quality_tier": quality_tier,
        "score_range": tier_info.get("score_range", (0, 0)),
        "priority": tier_info.get("priority", "unknown"),
        "success_probability": tier_info.get("success_probability", 0),
        "estimated_savings_range": tier_info.get("estimated_savings", (0, 0)),
        "typical_characteristics": tier_info.get("characteristics", [])
    }