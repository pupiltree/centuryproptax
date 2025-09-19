"""
Multi-Property Portfolio Management Scenarios for Demo Environment
Realistic conversation flows for complex property portfolio management and consolidated services
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import random
from datetime import datetime, timedelta

from agents.core.conversation_flows import ConversationStage, PropertyTaxConcern
from mock_data.property_records import get_sample_properties

class PortfolioType(Enum):
    """Types of property portfolios"""
    RESIDENTIAL_RENTAL = "residential_rental"
    COMMERCIAL_MIXED = "commercial_mixed"
    AGRICULTURAL_MIXED = "agricultural_mixed"
    MULTI_FAMILY = "multi_family"
    RETAIL_COMMERCIAL = "retail_commercial"
    INDUSTRIAL = "industrial"

class PortfolioComplexity(Enum):
    """Portfolio complexity levels"""
    SIMPLE = "simple"  # 2-5 properties, same county
    MODERATE = "moderate"  # 6-15 properties, multiple counties
    COMPLEX = "complex"  # 15+ properties, multiple states/types

@dataclass
class MultiPropertyScenario:
    """Multi-property management scenario with realistic conversation flow"""
    scenario_id: str
    portfolio_type: PortfolioType
    complexity: PortfolioComplexity
    customer_persona: str
    property_count: int
    total_assessment_value: float
    annual_tax_amount: float
    conversation_flow: List[Dict[str, str]]
    expected_response_elements: List[str]
    demo_notes: str
    portfolio_challenge: str
    demo_complexity_features: List[str]

class MultiPropertyDemoScenarios:
    """Demo scenarios for multi-property portfolio management"""

    def __init__(self):
        self.properties = get_sample_properties()
        self.scenarios = self._generate_scenarios()

    def _generate_scenarios(self) -> List[MultiPropertyScenario]:
        """Generate realistic multi-property management scenarios"""
        scenarios = []

        # Simple Portfolio Scenarios
        scenarios.extend(self._create_simple_portfolio_scenarios())

        # Moderate Portfolio Scenarios
        scenarios.extend(self._create_moderate_portfolio_scenarios())

        # Complex Portfolio Scenarios
        scenarios.extend(self._create_complex_portfolio_scenarios())

        return scenarios

    def _create_simple_portfolio_scenarios(self) -> List[MultiPropertyScenario]:
        """Create simple portfolio management scenarios"""
        scenarios = []

        # Scenario 1: Small residential rental portfolio
        scenarios.append(MultiPropertyScenario(
            scenario_id="multi_001",
            portfolio_type=PortfolioType.RESIDENTIAL_RENTAL,
            complexity=PortfolioComplexity.SIMPLE,
            customer_persona="small_investor",
            property_count=3,
            total_assessment_value=785000.00,
            annual_tax_amount=21195.00,
            conversation_flow=[
                {
                    "user": "I own 3 rental properties in Travis County. Can I see all my property taxes in one place?",
                    "ai": "Absolutely! I can provide a consolidated view of your 3 rental properties in Travis County. Your total portfolio assessment is $785,000 with annual taxes of $21,195. Property A: $8,750, Property B: $6,890, Property C: $5,555. Would you like detailed breakdowns for each property?",
                    "demo_action": "portfolio_overview_display"
                },
                {
                    "user": "Can I pay all three properties at once?",
                    "ai": "Yes, I can create a consolidated payment for all three properties. You can pay the total $21,195 in one transaction, and I'll allocate the payments correctly to each property. You'll receive individual receipts for each property plus a consolidated statement for your records.",
                    "demo_action": "consolidated_payment_setup"
                },
                {
                    "user": "One of my properties has tenants who damaged it. Does that affect the assessment?",
                    "ai": "Property damage that significantly affects value can be grounds for an assessment appeal. You'll need documentation of the damage (photos, repair estimates) and evidence that it impacts market value. I can help you file an appeal for that specific property while keeping your other properties unaffected.",
                    "demo_action": "individual_property_appeal_guidance"
                },
                {
                    "user": "Can you set up automatic payments for all my properties?",
                    "ai": "Yes, I can set up automatic payments for your entire portfolio. You can choose to pay annually in October or split into quarterly installments. The system will automatically allocate payments to each property and provide you with detailed reporting for tax purposes.",
                    "demo_action": "portfolio_auto_payment_setup"
                }
            ],
            expected_response_elements=[
                "portfolio_consolidation",
                "individual_property_breakdown",
                "consolidated_payment_option",
                "per_property_appeal_capability",
                "automated_portfolio_management"
            ],
            portfolio_challenge="Managing multiple rental properties efficiently while maintaining individual property tracking",
            demo_complexity_features=[
                "Portfolio-level tax overview",
                "Consolidated payment processing",
                "Individual property management",
                "Rental property tax implications"
            ],
            demo_notes="Demonstrates basic portfolio management for small real estate investors"
        ))

        return scenarios

    def _create_moderate_portfolio_scenarios(self) -> List[MultiPropertyScenario]:
        """Create moderate complexity portfolio scenarios"""
        scenarios = []

        # Scenario 2: Mixed commercial and residential portfolio
        scenarios.append(MultiPropertyScenario(
            scenario_id="multi_002",
            portfolio_type=PortfolioType.COMMERCIAL_MIXED,
            complexity=PortfolioComplexity.MODERATE,
            customer_persona="experienced_investor",
            property_count=8,
            total_assessment_value=3250000.00,
            annual_tax_amount=87750.00,
            conversation_flow=[
                {
                    "user": "I have 8 properties across Dallas and Collin counties - 5 commercial and 3 residential. Can you give me a comprehensive overview?",
                    "ai": "I can provide a comprehensive portfolio analysis. Your 8 properties total $3.25M in assessed value with $87,750 in annual taxes. Dallas County (5 properties): $58,400 taxes, Collin County (3 properties): $29,350 taxes. Commercial properties average $12,580 annually, residential average $6,890. Would you like county-by-county or property-type breakdowns?",
                    "demo_action": "comprehensive_portfolio_analysis"
                },
                {
                    "user": "The tax rates seem different between counties. Can you explain the impact on my investment returns?",
                    "ai": "Excellent question! Dallas County's rate is 2.68% while Collin County is 2.42%. For your $150K commercial property, that's a $390 annual difference. Your Dallas properties generate higher rental income but pay more taxes. Overall, your Dallas properties show 8.2% ROI vs 9.1% in Collin County when factoring in tax differences.",
                    "demo_action": "cross_county_tax_analysis"
                },
                {
                    "user": "I'm thinking of appealing assessments on my commercial properties. Can I do multiple appeals at once?",
                    "ai": "Yes, you can file appeals for multiple properties, even across counties. Each property requires separate documentation, but I can help coordinate the process. Your commercial properties saw 12-18% assessment increases - good grounds for appeals. Would you like me to prioritize which properties have the strongest appeal cases?",
                    "demo_action": "multi_property_appeal_coordination"
                },
                {
                    "user": "Can you help me plan for next year's taxes and budget for potential increases?",
                    "ai": "Absolutely! Based on market trends, I project 6-8% assessment increases for your portfolio, adding $5,250-$7,000 to next year's taxes. Commercial properties face higher risk of increases. I can create a tax planning spreadsheet and set up quarterly savings recommendations to budget for these increases.",
                    "demo_action": "tax_planning_and_projections"
                }
            ],
            expected_response_elements=[
                "multi_county_portfolio_analysis",
                "property_type_comparisons",
                "cross_county_tax_rate_impact",
                "coordinated_appeal_management",
                "forward_looking_tax_planning"
            ],
            portfolio_challenge="Managing complex mixed-use portfolio across multiple counties with varying tax rates",
            demo_complexity_features=[
                "Multi-county tax analysis",
                "Property type segmentation",
                "ROI impact calculations",
                "Coordinated appeal strategies",
                "Predictive tax planning"
            ],
            demo_notes="Shows advanced portfolio analytics and cross-county management capabilities"
        ))

        return scenarios

    def _create_complex_portfolio_scenarios(self) -> List[MultiPropertyScenario]:
        """Create complex portfolio management scenarios"""
        scenarios = []

        # Scenario 3: Large institutional-level portfolio
        scenarios.append(MultiPropertyScenario(
            scenario_id="multi_003",
            portfolio_type=PortfolioType.RETAIL_COMMERCIAL,
            complexity=PortfolioComplexity.COMPLEX,
            customer_persona="institutional_investor",
            property_count=25,
            total_assessment_value=15750000.00,
            annual_tax_amount=425250.00,
            conversation_flow=[
                {
                    "user": "I manage a portfolio of 25 retail properties across Texas for an institutional investor. We need comprehensive tax management and reporting. Can your system handle this complexity?",
                    "ai": "Yes, our system is designed for institutional-level portfolio management. Your 25 retail properties totaling $15.75M in value with $425,250 in annual taxes can be managed comprehensively. I can provide county-level analysis, property performance metrics, tax efficiency reports, and automated compliance tracking.",
                    "demo_action": "institutional_portfolio_overview"
                },
                {
                    "user": "We need detailed reporting for our investors and quarterly board presentations. What kind of reports can you generate?",
                    "ai": "I can generate institutional-grade reports including: property-by-property performance analysis, county tax rate comparisons, assessment trend analysis, portfolio optimization recommendations, quarterly tax accrual reports, and investor-ready financial summaries. All reports can be automated and customized for your presentation needs.",
                    "demo_action": "institutional_reporting_capabilities"
                },
                {
                    "user": "Several properties are underperforming and we're considering disposition. How do taxes factor into our decision?",
                    "ai": "I can provide comprehensive tax impact analysis for disposition decisions. For underperforming properties, I'll analyze: current tax burden vs. market rent, assessment trends, appeal potential, and tax implications of sale vs. hold strategies. This helps optimize your portfolio from a tax efficiency perspective.",
                    "demo_action": "disposition_tax_analysis"
                },
                {
                    "user": "We want to implement automated tax monitoring and alerts for the entire portfolio. What capabilities do you offer?",
                    "ai": "I can set up comprehensive automated monitoring including: assessment increase alerts (>5% threshold), appeal deadline notifications, payment due reminders, tax rate change notifications, and performance benchmarking alerts. You'll receive executive dashboards and exception reporting for proactive portfolio management.",
                    "demo_action": "automated_portfolio_monitoring_setup"
                }
            ],
            expected_response_elements=[
                "institutional_scale_management",
                "comprehensive_reporting_suite",
                "investment_decision_support",
                "automated_monitoring_systems",
                "executive_level_insights"
            ],
            portfolio_challenge="Managing institutional-scale portfolio with sophisticated reporting and analysis requirements",
            demo_complexity_features=[
                "Institutional-grade reporting",
                "Performance benchmarking",
                "Disposition analysis tools",
                "Automated monitoring systems",
                "Executive dashboard insights"
            ],
            demo_notes="Demonstrates enterprise-level portfolio management with institutional investor features"
        ))

        # Scenario 4: Family office mixed portfolio with succession planning
        scenarios.append(MultiPropertyScenario(
            scenario_id="multi_004",
            portfolio_type=PortfolioType.AGRICULTURAL_MIXED,
            complexity=PortfolioComplexity.COMPLEX,
            customer_persona="family_office_manager",
            property_count=18,
            total_assessment_value=8950000.00,
            annual_tax_amount=178500.00,
            conversation_flow=[
                {
                    "user": "Our family office manages 18 properties including agricultural land, commercial buildings, and residential rentals. We're planning generational transfer. How do property taxes factor into succession planning?",
                    "ai": "Succession planning with mixed property portfolios requires careful tax consideration. Your 18 properties include agricultural exemptions worth $45,000 annually in tax savings. During transfer, maintaining exemptions is crucial. I can help analyze: transfer tax implications, exemption continuity requirements, and optimal timing for generational transitions.",
                    "demo_action": "succession_planning_tax_analysis"
                },
                {
                    "user": "The agricultural properties have been in the family for generations. What happens to the ag exemptions during transfer to the next generation?",
                    "ai": "Agricultural exemptions can continue through family transfers if the new owners maintain qualifying agricultural use. Key requirements: continued agricultural production, minimum acreage compliance, and timely exemption renewal. I can help document transfer procedures and ensure exemption continuity saves your family $45,000+ annually.",
                    "demo_action": "agricultural_exemption_transfer_guidance"
                },
                {
                    "user": "We're considering placing some properties in trusts or LLCs. How does this affect property tax obligations and exemptions?",
                    "ai": "Entity structure changes can impact exemptions and tax obligations. Agricultural exemptions may continue in family trusts, but homestead exemptions are lost when transferred to LLCs. I can provide entity-by-entity analysis showing tax implications and recommend optimal structures to minimize family tax burden while achieving estate planning goals.",
                    "demo_action": "entity_structure_tax_impact_analysis"
                },
                {
                    "user": "Can you help us model different scenarios for the family property transition over the next 10 years?",
                    "ai": "Yes, I can create comprehensive 10-year modeling scenarios showing: gradual vs. immediate transfer tax impacts, exemption preservation strategies, assessment growth projections, and total family tax optimization. This helps your family make informed decisions about timing and structure of the generational transition.",
                    "demo_action": "long_term_family_planning_scenarios"
                }
            ],
            expected_response_elements=[
                "succession_planning_integration",
                "agricultural_exemption_continuity",
                "entity_structure_impact_analysis",
                "generational_tax_optimization",
                "long_term_scenario_modeling"
            ],
            portfolio_challenge="Complex family wealth management with generational transfer considerations and mixed property types",
            demo_complexity_features=[
                "Family succession planning tools",
                "Agricultural exemption management",
                "Entity structure analysis",
                "Generational tax modeling",
                "Wealth preservation strategies"
            ],
            demo_notes="Shows sophisticated family office capabilities with generational wealth management"
        ))

        return scenarios

    def get_scenario_by_id(self, scenario_id: str) -> Optional[MultiPropertyScenario]:
        """Get a specific scenario by ID"""
        for scenario in self.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        return None

    def get_scenarios_by_portfolio_type(self, portfolio_type: PortfolioType) -> List[MultiPropertyScenario]:
        """Get scenarios by portfolio type"""
        return [s for s in self.scenarios if s.portfolio_type == portfolio_type]

    def get_scenarios_by_complexity(self, complexity: PortfolioComplexity) -> List[MultiPropertyScenario]:
        """Get scenarios by complexity level"""
        return [s for s in self.scenarios if s.complexity == complexity]

    def get_scenarios_by_persona(self, persona: str) -> List[MultiPropertyScenario]:
        """Get scenarios for a specific customer persona"""
        return [s for s in self.scenarios if s.customer_persona == persona]

    def get_random_scenario(self) -> MultiPropertyScenario:
        """Get a random scenario for spontaneous demos"""
        return random.choice(self.scenarios)

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get summary of all portfolio scenarios"""
        return {
            "total_scenarios": len(self.scenarios),
            "by_portfolio_type": {
                portfolio_type.value: len(self.get_scenarios_by_portfolio_type(portfolio_type))
                for portfolio_type in PortfolioType
            },
            "by_complexity": {
                complexity.value: len(self.get_scenarios_by_complexity(complexity))
                for complexity in PortfolioComplexity
            },
            "total_properties": sum(s.property_count for s in self.scenarios),
            "total_portfolio_value": sum(s.total_assessment_value for s in self.scenarios),
            "average_property_count": sum(s.property_count for s in self.scenarios) / len(self.scenarios)
        }

    def get_all_scenarios(self) -> List[MultiPropertyScenario]:
        """Get all multi-property scenarios"""
        return self.scenarios

# Demo scenario manager
demo_multi_property_scenarios = MultiPropertyDemoScenarios()