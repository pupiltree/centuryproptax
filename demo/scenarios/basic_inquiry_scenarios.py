"""
Basic Property Tax Inquiry Scenarios for Demo Environment
Realistic conversation flows for common property tax information requests
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import random
from datetime import datetime, timedelta

from agents.core.conversation_flows import ConversationStage, PropertyTaxConcern
from mock_data.property_records import get_sample_properties, get_property_by_address
from mock_data.tax_rates import get_tax_rates_by_county
from mock_data.tax_calendars import get_tax_calendar_by_county

class InquiryType(Enum):
    """Types of basic property tax inquiries"""
    PROPERTY_VALUE = "property_value"
    TAX_AMOUNT = "tax_amount"
    PAYMENT_DUE_DATE = "payment_due_date"
    TAX_RATE = "tax_rate"
    EXEMPTION_STATUS = "exemption_status"
    ASSESSMENT_HISTORY = "assessment_history"
    PAYMENT_OPTIONS = "payment_options"
    CONTACT_INFO = "contact_info"

@dataclass
class BasicInquiryScenario:
    """Basic inquiry scenario with realistic conversation flow"""
    scenario_id: str
    inquiry_type: InquiryType
    customer_persona: str
    property_address: str
    county: str
    conversation_flow: List[Dict[str, str]]
    expected_response_elements: List[str]
    demo_notes: str

class BasicInquiryDemoScenarios:
    """Demo scenarios for basic property tax inquiries"""

    def __init__(self):
        self.properties = get_sample_properties()
        self.scenarios = self._generate_scenarios()

    def _generate_scenarios(self) -> List[BasicInquiryScenario]:
        """Generate realistic basic inquiry scenarios"""
        scenarios = []

        # Property Value Inquiry Scenarios
        scenarios.extend(self._create_property_value_scenarios())

        # Tax Amount Inquiry Scenarios
        scenarios.extend(self._create_tax_amount_scenarios())

        # Payment Due Date Scenarios
        scenarios.extend(self._create_payment_due_scenarios())

        # Tax Rate Inquiry Scenarios
        scenarios.extend(self._create_tax_rate_scenarios())

        # Exemption Status Scenarios
        scenarios.extend(self._create_exemption_scenarios())

        # Payment Options Scenarios
        scenarios.extend(self._create_payment_options_scenarios())

        return scenarios

    def _create_property_value_scenarios(self) -> List[BasicInquiryScenario]:
        """Create property value inquiry scenarios"""
        scenarios = []

        # Scenario 1: First-time homeowner asking about property value
        property = self.properties[0]
        scenarios.append(BasicInquiryScenario(
            scenario_id="basic_001",
            inquiry_type=InquiryType.PROPERTY_VALUE,
            customer_persona="first_time_homeowner",
            property_address=property["address"],
            county=property["county"],
            conversation_flow=[
                {
                    "user": "Hi, I just bought a house at 123 Oak Street in Dallas. Can you tell me what my property is valued at for tax purposes?",
                    "ai": "Hello! Congratulations on your new home. I'd be happy to help you with your property tax valuation. Let me look up the current assessed value for 123 Oak Street in Dallas County.",
                    "demo_action": "property_lookup"
                },
                {
                    "user": "Is this the market value or the assessed value?",
                    "ai": "Great question! This is the assessed value, which is what your property taxes are based on. In Texas, the assessed value should be close to market value, but there can be differences. The assessed value for your property is $285,000, which means your annual property taxes will be calculated on this amount.",
                    "demo_action": "value_explanation"
                },
                {
                    "user": "How often does this value get updated?",
                    "ai": "Property assessments in Dallas County are conducted annually. The appraisal district reviews property values each year and sends out new assessments typically in April or May. If you believe your assessment is too high, you have the right to appeal it before the deadline, which is usually in late May.",
                    "demo_action": "assessment_schedule_info"
                }
            ],
            expected_response_elements=[
                "property_address_confirmation",
                "assessed_value_amount",
                "county_information",
                "assessment_schedule",
                "appeal_rights_mention"
            ],
            demo_notes="Demonstrates property lookup, value explanation, and basic appeal process info"
        ))

        # Scenario 2: Experienced property owner checking multiple properties
        scenarios.append(BasicInquiryScenario(
            scenario_id="basic_002",
            inquiry_type=InquiryType.PROPERTY_VALUE,
            customer_persona="multi_property_owner",
            property_address="456 Commercial Blvd, Houston",
            county="Harris",
            conversation_flow=[
                {
                    "user": "I own several properties in Harris County. Can you give me the current assessed values for 456 Commercial Blvd in Houston?",
                    "ai": "I can help you with that. For your commercial property at 456 Commercial Blvd in Houston, Harris County, the current assessed value is $847,500. This includes both the land value of $185,000 and improvement value of $662,500.",
                    "demo_action": "commercial_property_lookup"
                },
                {
                    "user": "How does this compare to last year's assessment?",
                    "ai": "Looking at the assessment history, last year your property was assessed at $795,000, so there's been an increase of $52,500 or about 6.6%. This is within the typical range for commercial properties in this area of Houston.",
                    "demo_action": "assessment_comparison"
                },
                {
                    "user": "Can I get a breakdown of all my properties at once?",
                    "ai": "Absolutely! I can provide a portfolio view of all your properties. To do this efficiently, I can either look them up by your owner account number, or you can provide me with the addresses of your other properties. Would you prefer to give me your owner account number?",
                    "demo_action": "portfolio_management_offer"
                }
            ],
            expected_response_elements=[
                "commercial_property_identification",
                "land_vs_improvement_breakdown",
                "year_over_year_comparison",
                "portfolio_management_option"
            ],
            demo_notes="Shows commercial property handling and portfolio management capabilities"
        ))

        return scenarios

    def _create_tax_amount_scenarios(self) -> List[BasicInquiryScenario]:
        """Create tax amount calculation scenarios"""
        scenarios = []

        # Scenario 3: Homeowner asking about annual tax amount
        scenarios.append(BasicInquiryScenario(
            scenario_id="basic_003",
            inquiry_type=InquiryType.TAX_AMOUNT,
            customer_persona="homeowner_with_exemptions",
            property_address="789 Pine Lane, Austin",
            county="Travis",
            conversation_flow=[
                {
                    "user": "What will my property taxes be this year for 789 Pine Lane in Austin?",
                    "ai": "I can help you calculate your property taxes. Your property at 789 Pine Lane in Austin is assessed at $425,000. With your homestead exemption of $100,000, your taxable value is $325,000. Based on the current tax rates for Travis County, your total annual property tax will be approximately $8,775.",
                    "demo_action": "tax_calculation_with_exemptions"
                },
                {
                    "user": "Can you break down which entities get what portion?",
                    "ai": "Certainly! Here's your tax breakdown: Travis County: $1,950, Austin ISD: $4,225, City of Austin: $1,430, Travis County Healthcare District: $520, Austin Community College: $650. The largest portion goes to the school district, which is typical in Texas.",
                    "demo_action": "tax_entity_breakdown"
                },
                {
                    "user": "When do I need to pay this?",
                    "ai": "Your taxes become due on October 1st and are delinquent if not paid by January 31st of the following year. You can pay the full amount by January 31st, or if you qualify, you can split it into installments. Would you like information about installment payment options?",
                    "demo_action": "payment_timeline_info"
                }
            ],
            expected_response_elements=[
                "assessed_value",
                "exemption_deduction",
                "taxable_value",
                "total_tax_amount",
                "entity_breakdown",
                "payment_timeline"
            ],
            demo_notes="Demonstrates tax calculation with exemptions and entity breakdown"
        ))

        return scenarios

    def _create_payment_due_scenarios(self) -> List[BasicInquiryScenario]:
        """Create payment due date scenarios"""
        scenarios = []

        # Scenario 4: Senior citizen asking about payment deadlines
        scenarios.append(BasicInquiryScenario(
            scenario_id="basic_004",
            inquiry_type=InquiryType.PAYMENT_DUE_DATE,
            customer_persona="senior_citizen",
            property_address="321 Elm Street, San Antonio",
            county="Bexar",
            conversation_flow=[
                {
                    "user": "When are my property taxes due? I live at 321 Elm Street in San Antonio and I'm 67 years old.",
                    "ai": "Your property taxes for 321 Elm Street in San Antonio are due on October 1st and become delinquent after January 31st if not paid. However, since you're over 65, you may qualify for additional protections and payment options. You cannot lose your home for unpaid taxes if you're current on any payment plan you've arranged.",
                    "demo_action": "senior_payment_timeline"
                },
                {
                    "user": "What happens if I can't pay the full amount by January 31st?",
                    "ai": "As a senior, you have several options. You can request a payment plan to spread the payments over the year, or if you're facing financial hardship, you may qualify for a tax deferral program that allows you to postpone payment until the property is sold or transferred. Would you like me to explain these options in more detail?",
                    "demo_action": "senior_payment_options"
                },
                {
                    "user": "Yes, tell me about the deferral program.",
                    "ai": "The tax deferral program for seniors allows you to defer your taxes if you're 65 or older and meet income requirements. The deferred taxes accrue 5% interest annually, but you won't face foreclosure. The taxes become due when the property is sold or ownership changes. To apply, you'll need to file a deferral affidavit with Bexar County by the payment deadline.",
                    "demo_action": "deferral_program_explanation"
                }
            ],
            expected_response_elements=[
                "standard_payment_timeline",
                "senior_citizen_protections",
                "payment_plan_options",
                "deferral_program_details",
                "application_process"
            ],
            demo_notes="Shows senior-specific tax payment options and protections"
        ))

        return scenarios

    def _create_tax_rate_scenarios(self) -> List[BasicInquiryScenario]:
        """Create tax rate inquiry scenarios"""
        scenarios = []

        # Scenario 5: Business owner asking about commercial tax rates
        scenarios.append(BasicInquiryScenario(
            scenario_id="basic_005",
            inquiry_type=InquiryType.TAX_RATE,
            customer_persona="commercial_property_owner",
            property_address="555 Business Park Dr, Plano",
            county="Collin",
            conversation_flow=[
                {
                    "user": "What are the current property tax rates for commercial property in Plano?",
                    "ai": "For commercial properties in Plano, Collin County, the total tax rate is approximately $2.68 per $100 of assessed value. This breaks down as: Collin County: $0.2325, Plano ISD: $1.1685, City of Plano: $0.4594, Collin College: $0.1542, and other districts: $0.6654.",
                    "demo_action": "commercial_tax_rates"
                },
                {
                    "user": "How does this compare to residential rates in the same area?",
                    "ai": "Residential and commercial properties in Plano have the same tax rates per $100 of valuation. However, residential properties often benefit from homestead exemptions that reduce their taxable value, while commercial properties typically don't qualify for these exemptions. So while the rates are the same, the effective tax burden is often higher for commercial properties.",
                    "demo_action": "rate_comparison_explanation"
                },
                {
                    "user": "Are there any tax incentives available for businesses?",
                    "ai": "Yes, there are several potential incentives. The City of Plano offers economic development incentives for qualifying businesses, including tax abatements for new construction or significant improvements. Collin County also has programs for manufacturing and technology companies. Would you like information about specific incentive programs that might apply to your business?",
                    "demo_action": "business_incentive_info"
                }
            ],
            expected_response_elements=[
                "commercial_tax_rates",
                "rate_breakdown_by_entity",
                "residential_vs_commercial_comparison",
                "available_incentives",
                "qualification_criteria"
            ],
            demo_notes="Demonstrates commercial tax rate information and business incentives"
        ))

        return scenarios

    def _create_exemption_scenarios(self) -> List[BasicInquiryScenario]:
        """Create exemption status scenarios"""
        scenarios = []

        # Scenario 6: New homeowner asking about homestead exemption
        scenarios.append(BasicInquiryScenario(
            scenario_id="basic_006",
            inquiry_type=InquiryType.EXEMPTION_STATUS,
            customer_persona="new_homeowner",
            property_address="888 Maple Drive, Fort Worth",
            county="Tarrant",
            conversation_flow=[
                {
                    "user": "I just moved to Fort Worth and bought a house at 888 Maple Drive. Do I have a homestead exemption?",
                    "ai": "Let me check your exemption status. I see that your property at 888 Maple Drive in Fort Worth doesn't currently have a homestead exemption filed. Since you've just moved in, you'll need to apply for this exemption with the Tarrant County Appraisal District to reduce your taxable value.",
                    "demo_action": "exemption_status_check"
                },
                {
                    "user": "How much money will the homestead exemption save me?",
                    "ai": "In Tarrant County, the homestead exemption removes $100,000 from your home's taxable value. With your home's assessed value of $375,000 and the current tax rate of about $2.42 per $100, the homestead exemption will save you approximately $2,420 annually in property taxes.",
                    "demo_action": "exemption_savings_calculation"
                },
                {
                    "user": "What do I need to do to apply?",
                    "ai": "You'll need to file an Application for Residential Homestead Exemption with the Tarrant County Appraisal District. You can do this online, by mail, or in person. You'll need to provide proof of ownership and evidence that this is your primary residence as of January 1st. The deadline to apply is April 30th, but since you just moved, you may qualify for a late application.",
                    "demo_action": "exemption_application_process"
                }
            ],
            expected_response_elements=[
                "current_exemption_status",
                "exemption_value_amount",
                "annual_savings_calculation",
                "application_requirements",
                "deadline_information"
            ],
            demo_notes="Shows exemption checking and application guidance"
        ))

        return scenarios

    def _create_payment_options_scenarios(self) -> List[BasicInquiryScenario]:
        """Create payment options scenarios"""
        scenarios = []

        # Scenario 7: Property owner asking about installment payments
        scenarios.append(BasicInquiryScenario(
            scenario_id="basic_007",
            inquiry_type=InquiryType.PAYMENT_OPTIONS,
            customer_persona="cash_flow_conscious_owner",
            property_address="777 Cedar Lane, Richardson",
            county="Dallas",
            conversation_flow=[
                {
                    "user": "Can I pay my property taxes in installments? My property is at 777 Cedar Lane in Richardson.",
                    "ai": "Yes, Dallas County offers installment payment options. For your property at 777 Cedar Lane, you can split your $6,840 annual tax bill into four quarterly payments if you apply by the deadline. This would be approximately $1,710 per quarter, plus a small processing fee.",
                    "demo_action": "installment_option_explanation"
                },
                {
                    "user": "When would the payments be due and is there interest?",
                    "ai": "The quarterly payments would be due on October 1st, December 1st, February 1st, and April 1st. There's no additional interest charged if you make all payments on time, just a one-time $25 application fee. However, if you miss a payment, the entire remaining balance becomes due immediately.",
                    "demo_action": "installment_schedule_details"
                },
                {
                    "user": "What other payment methods do you accept?",
                    "ai": "Dallas County accepts several payment methods: online payments by bank transfer (ACH) or credit card, payments by phone, mail with check or money order, and in-person payments at tax offices. Online and credit card payments have small convenience fees. You can also set up automatic payments if you choose the installment plan.",
                    "demo_action": "payment_methods_overview"
                }
            ],
            expected_response_elements=[
                "installment_eligibility",
                "quarterly_payment_amounts",
                "payment_schedule",
                "fees_and_interest",
                "available_payment_methods"
            ],
            demo_notes="Demonstrates payment flexibility and options"
        ))

        return scenarios

    def get_scenario_by_id(self, scenario_id: str) -> Optional[BasicInquiryScenario]:
        """Get a specific scenario by ID"""
        for scenario in self.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        return None

    def get_scenarios_by_type(self, inquiry_type: InquiryType) -> List[BasicInquiryScenario]:
        """Get all scenarios of a specific type"""
        return [s for s in self.scenarios if s.inquiry_type == inquiry_type]

    def get_scenarios_by_persona(self, persona: str) -> List[BasicInquiryScenario]:
        """Get all scenarios for a specific customer persona"""
        return [s for s in self.scenarios if s.customer_persona == persona]

    def get_random_scenario(self) -> BasicInquiryScenario:
        """Get a random scenario for spontaneous demos"""
        return random.choice(self.scenarios)

    def get_all_scenarios(self) -> List[BasicInquiryScenario]:
        """Get all basic inquiry scenarios"""
        return self.scenarios

# Demo scenario manager
demo_basic_scenarios = BasicInquiryDemoScenarios()