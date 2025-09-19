"""
Assessment Appeal Scenarios for Demo Environment
Realistic conversation flows for property tax assessment appeals and disputes
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import random
from datetime import datetime, timedelta

from agents.core.conversation_flows import ConversationStage, PropertyTaxConcern
from mock_data.property_records import get_sample_properties
from mock_data.assessment_patterns import get_assessment_patterns_by_county

class AppealScenarioType(Enum):
    """Types of assessment appeal scenarios"""
    RESIDENTIAL_APPEAL = "residential_appeal"
    COMMERCIAL_APPEAL = "commercial_appeal"
    DEADLINE_INQUIRY = "deadline_inquiry"
    EVIDENCE_GATHERING = "evidence_gathering"
    APPEAL_STATUS = "appeal_status"
    INFORMAL_CONFERENCE = "informal_conference"
    FORMAL_HEARING = "formal_hearing"
    POST_APPEAL = "post_appeal"

@dataclass
class AssessmentAppealScenario:
    """Assessment appeal scenario with realistic conversation flow"""
    scenario_id: str
    scenario_type: AppealScenarioType
    customer_persona: str
    property_address: str
    county: str
    current_assessment: float
    disputed_assessment: float
    conversation_flow: List[Dict[str, str]]
    expected_response_elements: List[str]
    demo_notes: str
    legal_complexity: str  # "simple", "moderate", "complex"

class AssessmentAppealDemoScenarios:
    """Demo scenarios for assessment appeal processes"""

    def __init__(self):
        self.properties = get_sample_properties()
        self.scenarios = self._generate_scenarios()

    def _generate_scenarios(self) -> List[AssessmentAppealScenario]:
        """Generate realistic assessment appeal scenarios"""
        scenarios = []

        # Residential Appeal Scenarios
        scenarios.extend(self._create_residential_appeal_scenarios())

        # Commercial Appeal Scenarios
        scenarios.extend(self._create_commercial_appeal_scenarios())

        # Deadline and Process Inquiry Scenarios
        scenarios.extend(self._create_deadline_scenarios())

        # Evidence Gathering Scenarios
        scenarios.extend(self._create_evidence_scenarios())

        # Appeal Status and Tracking Scenarios
        scenarios.extend(self._create_status_scenarios())

        return scenarios

    def _create_residential_appeal_scenarios(self) -> List[AssessmentAppealScenario]:
        """Create residential property appeal scenarios"""
        scenarios = []

        # Scenario 1: Homeowner believes assessment is too high
        scenarios.append(AssessmentAppealScenario(
            scenario_id="appeal_001",
            scenario_type=AppealScenarioType.RESIDENTIAL_APPEAL,
            customer_persona="concerned_homeowner",
            property_address="123 Overvalued Lane, Austin",
            county="Travis",
            current_assessment=485000.00,
            disputed_assessment=425000.00,
            conversation_flow=[
                {
                    "user": "My property assessment went up 25% this year to $485,000, but I don't think my house is worth that much. How do I appeal this?",
                    "ai": "I understand your concern about the significant increase in your assessment. A 25% increase is substantial and definitely worth investigating. In Travis County, you have the right to appeal your assessment. The deadline for filing an appeal is typically May 15th, and I can help you understand the process.",
                    "demo_action": "appeal_process_overview"
                },
                {
                    "user": "What evidence do I need to support my appeal?",
                    "ai": "Great question! For a successful appeal, you'll want to gather: recent sales of similar homes in your neighborhood (comparables), photos showing any property conditions that might affect value, documentation of any needed repairs, and possibly a professional appraisal. The key is proving your home's market value is lower than the assessed value.",
                    "demo_action": "evidence_requirements_explanation"
                },
                {
                    "user": "I saw that my neighbor's similar house sold for $425,000 last month. Would that help my case?",
                    "ai": "Absolutely! That's excellent evidence, especially if the houses are truly comparable in size, age, and condition. Recent sales within a half-mile radius are given significant weight. I'd recommend gathering 3-5 similar sales if possible. You'll want to document: sale date, sale price, square footage, lot size, age, and condition compared to your property.",
                    "demo_action": "comparable_sales_guidance"
                },
                {
                    "user": "How do I actually file the appeal? Is there a deadline?",
                    "ai": "You can file your appeal online through the Travis County Appraisal District website, by mail, or in person. The deadline is May 15th - that's just 18 days away, so time is important. The filing is free, and you'll receive a confirmation with your hearing date. Would you like me to help you start the online filing process?",
                    "demo_action": "filing_process_assistance"
                }
            ],
            expected_response_elements=[
                "appeal_deadline_awareness",
                "evidence_requirements",
                "comparable_sales_importance",
                "filing_process_options",
                "urgency_communication"
            ],
            legal_complexity="simple",
            demo_notes="Shows standard residential appeal process with emphasis on deadline urgency"
        ))

        # Scenario 2: Homeowner confused about informal vs formal hearing
        scenarios.append(AssessmentAppealScenario(
            scenario_id="appeal_002",
            scenario_type=AppealScenarioType.INFORMAL_CONFERENCE,
            customer_persona="process_oriented_homeowner",
            property_address="456 Process Drive, Dallas",
            county="Dallas",
            current_assessment=325000.00,
            disputed_assessment=295000.00,
            conversation_flow=[
                {
                    "user": "I filed my appeal and got a notice about an informal conference vs. a formal hearing. What's the difference?",
                    "ai": "Good question! An informal conference is usually your first step - it's a casual meeting with an appraiser to discuss your concerns. It's less formal, no sworn testimony required, and often resolves disputes quickly. If you're not satisfied with the result, you can then request a formal hearing before the Appraisal Review Board.",
                    "demo_action": "hearing_types_explanation"
                },
                {
                    "user": "Which one should I choose? My case seems pretty straightforward.",
                    "ai": "For most residential appeals like yours, I'd recommend starting with the informal conference. It's faster, less intimidating, and the appraiser can often resolve the issue on the spot if your evidence is solid. Since you have good comparable sales data showing similar homes selling for around $295,000, the informal conference might be all you need.",
                    "demo_action": "recommendation_based_on_case"
                },
                {
                    "user": "What should I bring to the informal conference?",
                    "ai": "Bring printed copies of: your comparable sales data with photos and details, any recent appraisal you might have, photos of your property showing current condition, and any documentation of needed repairs. Be prepared to explain why you think $295,000 is more accurate than $325,000. Keep it factual and organized.",
                    "demo_action": "conference_preparation_checklist"
                }
            ],
            expected_response_elements=[
                "informal_vs_formal_distinction",
                "process_recommendation",
                "evidence_preparation",
                "meeting_expectations"
            ],
            legal_complexity="simple",
            demo_notes="Explains the two-tier appeal process and preparation requirements"
        ))

        return scenarios

    def _create_commercial_appeal_scenarios(self) -> List[AssessmentAppealScenario]:
        """Create commercial property appeal scenarios"""
        scenarios = []

        # Scenario 3: Commercial property owner with complex appeal
        scenarios.append(AssessmentAppealScenario(
            scenario_id="appeal_003",
            scenario_type=AppealScenarioType.COMMERCIAL_APPEAL,
            customer_persona="commercial_property_owner",
            property_address="789 Business Plaza, Houston",
            county="Harris",
            current_assessment=2450000.00,
            disputed_assessment=2100000.00,
            conversation_flow=[
                {
                    "user": "My commercial property assessment jumped from $2.1M to $2.45M this year. The building has significant deferred maintenance and vacancy issues. How do I appeal this?",
                    "ai": "Commercial appeals are more complex than residential ones, and your situation with deferred maintenance and vacancy issues provides strong grounds for appeal. In Harris County, commercial appeals often require professional appraisals and detailed financial documentation. The key is proving the assessment doesn't reflect the property's actual market value.",
                    "demo_action": "commercial_appeal_complexity_explanation"
                },
                {
                    "user": "What kind of evidence will I need for a commercial appeal?",
                    "ai": "For commercial properties, you'll need: a professional appraisal (highly recommended), rent roll showing actual vs. potential income, operating expense documentation, photos documenting deferred maintenance, comparable sales or leases of similar commercial properties, and vacancy analysis. The income approach is often key for commercial valuations.",
                    "demo_action": "commercial_evidence_requirements"
                },
                {
                    "user": "Should I hire a professional to handle this appeal?",
                    "ai": "Given the complexity and the $350,000 difference in assessment, I'd strongly recommend consulting with a property tax consultant or attorney who specializes in commercial appeals. They understand the technical aspects of commercial valuation and can present your case more effectively. The potential tax savings often justify the professional fees.",
                    "demo_action": "professional_representation_recommendation"
                },
                {
                    "user": "How long does the commercial appeal process typically take?",
                    "ai": "Commercial appeals typically take 3-6 months from filing to resolution, depending on the complexity and whether you go through informal conference, formal hearing, or both. If the case goes to district court (rare but possible for large commercial properties), it could take 12-18 months. Most cases settle at the informal conference or ARB level.",
                    "demo_action": "commercial_timeline_explanation"
                }
            ],
            expected_response_elements=[
                "commercial_complexity_acknowledgment",
                "professional_appraisal_importance",
                "income_approach_explanation",
                "professional_representation_value",
                "realistic_timeline_expectations"
            ],
            legal_complexity="complex",
            demo_notes="Demonstrates commercial appeal complexity and professional guidance needs"
        ))

        return scenarios

    def _create_deadline_scenarios(self) -> List[AssessmentAppealScenario]:
        """Create deadline and timing inquiry scenarios"""
        scenarios = []

        # Scenario 4: Property owner asking about missed deadlines
        scenarios.append(AssessmentAppealScenario(
            scenario_id="appeal_004",
            scenario_type=AppealScenarioType.DEADLINE_INQUIRY,
            customer_persona="late_discoverer",
            property_address="321 Missed Deadline St, San Antonio",
            county="Bexar",
            current_assessment=375000.00,
            disputed_assessment=340000.00,
            conversation_flow=[
                {
                    "user": "I just realized my property assessment is too high, but I think I missed the appeal deadline. Is there anything I can do?",
                    "ai": "Let me check the current date and deadlines for Bexar County. The standard appeal deadline was May 15th, which has passed. However, there may still be options available depending on your specific circumstances. Late appeals are sometimes accepted under certain conditions.",
                    "demo_action": "deadline_status_check"
                },
                {
                    "user": "What are those conditions? I just got divorced and was dealing with a lot of personal issues.",
                    "ai": "Personal circumstances like divorce, illness, or other significant life events can sometimes qualify for a late appeal. Bexar County may accept late appeals if you can show 'good cause' for missing the deadline. You'd need to file a motion explaining the circumstances and provide documentation. The deadline for late appeals with good cause is typically July 25th.",
                    "demo_action": "good_cause_explanation"
                },
                {
                    "user": "How do I file for a late appeal? What documentation do I need?",
                    "ai": "You'll need to file a 'Motion for Late Appeal' with the Appraisal Review Board, explaining your circumstances and providing supporting documentation (like divorce papers, medical records, etc.). You'll also need to file your regular appeal documents. I'd recommend acting quickly since the late appeal deadline is also firm. Would you like help starting this process?",
                    "demo_action": "late_appeal_filing_assistance"
                }
            ],
            expected_response_elements=[
                "deadline_status_confirmation",
                "good_cause_criteria",
                "late_appeal_options",
                "required_documentation",
                "urgency_for_late_filing"
            ],
            legal_complexity="moderate",
            demo_notes="Shows deadline flexibility and late appeal procedures"
        ))

        return scenarios

    def _create_evidence_scenarios(self) -> List[AssessmentAppealScenario]:
        """Create evidence gathering and preparation scenarios"""
        scenarios = []

        # Scenario 5: Property owner seeking help with evidence preparation
        scenarios.append(AssessmentAppealScenario(
            scenario_id="appeal_005",
            scenario_type=AppealScenarioType.EVIDENCE_GATHERING,
            customer_persona="detail_oriented_homeowner",
            property_address="555 Evidence Court, Plano",
            county="Collin",
            current_assessment=445000.00,
            disputed_assessment=415000.00,
            conversation_flow=[
                {
                    "user": "I want to appeal my assessment but I'm not sure I have enough evidence. Can you help me understand what makes a strong case?",
                    "ai": "I'd be happy to help you build a strong appeal case. The best evidence includes recent sales of truly comparable properties, current market conditions, and any specific issues with your property. Let's start by looking at what comparable sales data you might need for your property in Plano.",
                    "demo_action": "evidence_strength_assessment"
                },
                {
                    "user": "How do I find comparable sales? And how similar do they need to be?",
                    "ai": "For comparable sales, look for properties within a half-mile radius that sold within the last 12 months. They should be similar in: square footage (within 10-15%), lot size, age (within 5-10 years), style, and condition. The MLS, county records, and real estate websites like Zillow can help. I can also help you identify key comparables in your area.",
                    "demo_action": "comparable_sales_criteria"
                },
                {
                    "user": "My house has some unique features that might make it hard to compare. How do I handle that?",
                    "ai": "Unique features can actually work in your favor if they're properly documented. If your house has outdated features, needed repairs, or functional obsolescence, document these with photos and estimates. If it has premium features that add value, make sure the appraiser knows about them. The key is showing how your property differs from the assessed 'typical' property.",
                    "demo_action": "unique_feature_documentation"
                }
            ],
            expected_response_elements=[
                "evidence_quality_criteria",
                "comparable_property_standards",
                "documentation_techniques",
                "unique_feature_handling"
            ],
            legal_complexity="simple",
            demo_notes="Teaches effective evidence gathering and case preparation"
        ))

        return scenarios

    def _create_status_scenarios(self) -> List[AssessmentAppealScenario]:
        """Create appeal status and tracking scenarios"""
        scenarios = []

        # Scenario 6: Property owner checking appeal status
        scenarios.append(AssessmentAppealScenario(
            scenario_id="appeal_006",
            scenario_type=AppealScenarioType.APPEAL_STATUS,
            customer_persona="anxious_appellant",
            property_address="777 Waiting Way, Fort Worth",
            county="Tarrant",
            current_assessment=395000.00,
            disputed_assessment=365000.00,
            conversation_flow=[
                {
                    "user": "I filed my appeal three weeks ago and haven't heard anything. How can I check the status?",
                    "ai": "I understand your concern about the timeline. Let me check your appeal status for 777 Waiting Way in Fort Worth. Your appeal was filed on April 28th and is currently scheduled for an informal conference on June 15th. This timeline is normal - most counties take 4-6 weeks to schedule informal conferences.",
                    "demo_action": "appeal_status_lookup"
                },
                {
                    "user": "What should I expect at the informal conference? I'm nervous about it.",
                    "ai": "It's completely normal to feel nervous! The informal conference is actually quite relaxed. You'll meet with an appraiser for about 15-20 minutes to discuss your evidence. They'll review your comparable sales and listen to your concerns. Many appeals are resolved right at this meeting. Come prepared, but don't worry - it's a conversation, not an interrogation.",
                    "demo_action": "conference_expectation_setting"
                },
                {
                    "user": "What happens if they don't agree to lower my assessment at the informal conference?",
                    "ai": "If the informal conference doesn't resolve your appeal, you have options. You can accept their counter-offer if they make one, or you can request a formal hearing before the Appraisal Review Board. The formal hearing is more structured but still accessible to homeowners. You'll present your case to a three-person panel who will make the final decision.",
                    "demo_action": "next_steps_explanation"
                }
            ],
            expected_response_elements=[
                "current_appeal_status",
                "timeline_expectations",
                "process_reassurance",
                "next_step_options"
            ],
            legal_complexity="simple",
            demo_notes="Provides status updates and process reassurance"
        ))

        return scenarios

    def get_scenario_by_id(self, scenario_id: str) -> Optional[AssessmentAppealScenario]:
        """Get a specific scenario by ID"""
        for scenario in self.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        return None

    def get_scenarios_by_type(self, scenario_type: AppealScenarioType) -> List[AssessmentAppealScenario]:
        """Get all scenarios of a specific type"""
        return [s for s in self.scenarios if s.scenario_type == scenario_type]

    def get_scenarios_by_complexity(self, complexity: str) -> List[AssessmentAppealScenario]:
        """Get scenarios by legal complexity level"""
        return [s for s in self.scenarios if s.legal_complexity == complexity]

    def get_scenarios_by_persona(self, persona: str) -> List[AssessmentAppealScenario]:
        """Get all scenarios for a specific customer persona"""
        return [s for s in self.scenarios if s.customer_persona == persona]

    def get_random_scenario(self) -> AssessmentAppealScenario:
        """Get a random scenario for spontaneous demos"""
        return random.choice(self.scenarios)

    def get_all_scenarios(self) -> List[AssessmentAppealScenario]:
        """Get all assessment appeal scenarios"""
        return self.scenarios

# Demo scenario manager
demo_appeal_scenarios = AssessmentAppealDemoScenarios()