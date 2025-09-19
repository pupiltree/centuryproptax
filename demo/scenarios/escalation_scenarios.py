"""
Escalation Scenarios for Demo Environment
Realistic conversation flows for complex cases requiring human agent escalation
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import random
from datetime import datetime, timedelta

from agents.core.conversation_flows import ConversationStage, PropertyTaxConcern

class EscalationType(Enum):
    """Types of escalation scenarios"""
    COMPLEX_LEGAL = "complex_legal"
    TECHNICAL_ISSUE = "technical_issue"
    EMOTIONAL_DISTRESS = "emotional_distress"
    MULTI_JURISDICTION = "multi_jurisdiction"
    URGENT_DEADLINE = "urgent_deadline"
    SYSTEM_LIMITATION = "system_limitation"
    LANGUAGE_BARRIER = "language_barrier"
    SPECIAL_CIRCUMSTANCES = "special_circumstances"

class EscalationTrigger(Enum):
    """What triggers the escalation"""
    AI_CONFIDENCE_LOW = "ai_confidence_low"
    USER_REQUEST = "user_request"
    COMPLEXITY_THRESHOLD = "complexity_threshold"
    EMOTIONAL_INDICATORS = "emotional_indicators"
    LEGAL_ADVICE_NEEDED = "legal_advice_needed"
    SYSTEM_ERROR = "system_error"
    TIME_SENSITIVE = "time_sensitive"

@dataclass
class EscalationScenario:
    """Escalation scenario with realistic conversation flow and handoff process"""
    scenario_id: str
    escalation_type: EscalationType
    escalation_trigger: EscalationTrigger
    customer_persona: str
    property_address: str
    county: str
    urgency_level: str  # "low", "medium", "high", "critical"
    conversation_flow: List[Dict[str, str]]
    escalation_point: int  # Which conversation turn triggers escalation
    expected_response_elements: List[str]
    demo_notes: str
    handoff_information: Dict[str, Any]

class EscalationDemoScenarios:
    """Demo scenarios for AI-to-human escalation processes"""

    def __init__(self):
        self.scenarios = self._generate_scenarios()

    def _generate_scenarios(self) -> List[EscalationScenario]:
        """Generate realistic escalation scenarios"""
        scenarios = []

        # Complex Legal Escalations
        scenarios.extend(self._create_legal_escalation_scenarios())

        # Technical Issue Escalations
        scenarios.extend(self._create_technical_escalation_scenarios())

        # Emotional Distress Escalations
        scenarios.extend(self._create_emotional_escalation_scenarios())

        # Multi-Jurisdiction Escalations
        scenarios.extend(self._create_multi_jurisdiction_scenarios())

        # Urgent Deadline Escalations
        scenarios.extend(self._create_urgent_deadline_scenarios())

        # Language Barrier Escalations
        scenarios.extend(self._create_language_barrier_scenarios())

        return scenarios

    def _create_legal_escalation_scenarios(self) -> List[EscalationScenario]:
        """Create complex legal issue escalation scenarios"""
        scenarios = []

        # Scenario 1: Property rights dispute requiring legal interpretation
        scenarios.append(EscalationScenario(
            scenario_id="escalation_001",
            escalation_type=EscalationType.COMPLEX_LEGAL,
            escalation_trigger=EscalationTrigger.LEGAL_ADVICE_NEEDED,
            customer_persona="property_rights_disputant",
            property_address="123 Legal Issue Lane, Austin",
            county="Travis",
            urgency_level="high",
            conversation_flow=[
                {
                    "user": "My ex-husband put a lien on our jointly owned property for unpaid taxes, but I've been paying them. Can he do this legally?",
                    "ai": "I understand this is a complex situation involving property ownership, liens, and tax payments. This type of legal matter involving joint property ownership and spousal rights requires specific legal expertise that goes beyond general property tax guidance.",
                    "demo_action": "legal_complexity_recognition"
                },
                {
                    "user": "But I have all the payment receipts. Doesn't that prove I've been paying the taxes?",
                    "ai": "Your payment receipts are definitely important documentation. However, questions about property liens, joint ownership rights, and spousal property disputes involve specific legal interpretations that require a qualified attorney or legal expert to properly address.",
                    "demo_action": "acknowledge_evidence_but_maintain_boundaries"
                },
                {
                    "user": "Can't you just tell me if the lien is valid or not?",
                    "ai": "I understand your frustration, and I wish I could provide that determination, but lien validity involves complex legal analysis that I'm not qualified to perform. This situation requires professional legal assessment. Let me connect you with a human specialist who can review your documentation and provide appropriate guidance for your specific legal situation.",
                    "demo_action": "escalation_trigger_explanation"
                }
            ],
            escalation_point=3,
            expected_response_elements=[
                "legal_complexity_acknowledgment",
                "clear_boundary_explanation",
                "evidence_acknowledgment",
                "professional_referral_offer",
                "empathetic_tone_maintenance"
            ],
            handoff_information={
                "specialist_type": "Legal Affairs Specialist",
                "urgency": "High - Property lien dispute",
                "required_documents": ["Payment receipts", "Property deed", "Lien documentation"],
                "case_summary": "Joint property ownership dispute with tax lien complications requiring legal interpretation"
            },
            demo_notes="Demonstrates clear legal boundary recognition and professional escalation"
        ))

        return scenarios

    def _create_technical_escalation_scenarios(self) -> List[EscalationScenario]:
        """Create technical issue escalation scenarios"""
        scenarios = []

        # Scenario 2: System error preventing payment processing
        scenarios.append(EscalationScenario(
            scenario_id="escalation_002",
            escalation_type=EscalationType.TECHNICAL_ISSUE,
            escalation_trigger=EscalationTrigger.SYSTEM_ERROR,
            customer_persona="tech_frustrated_homeowner",
            property_address="456 System Error Street, Dallas",
            county="Dallas",
            urgency_level="medium",
            conversation_flow=[
                {
                    "user": "I've been trying to pay my property taxes online for three days and it keeps giving me an error message. The deadline is tomorrow!",
                    "ai": "I'm sorry you're experiencing difficulties with the online payment system. Let me check the status of our payment processing systems and see what specific error you're encountering. Can you tell me what error message you're seeing?",
                    "demo_action": "technical_troubleshooting_start"
                },
                {
                    "user": "It says 'Payment processing temporarily unavailable, error code 502.' I really need to pay this today!",
                    "ai": "Thank you for providing the error code. Error 502 indicates a server connectivity issue with our payment processor. I can see this is affecting multiple users currently. Since your payment deadline is tomorrow, this is definitely urgent. Let me immediately connect you with our technical support team who can process your payment through alternative methods.",
                    "demo_action": "system_error_confirmation_and_escalation"
                },
                {
                    "user": "Can they take my payment over the phone right now?",
                    "ai": "Yes, our technical support team can process phone payments and ensure your taxes are paid before the deadline. I'm escalating your case as urgent due to the timing. You'll be connected with a specialist within the next few minutes who can take your payment immediately and provide confirmation.",
                    "demo_action": "immediate_escalation_with_timeline"
                }
            ],
            escalation_point=2,
            expected_response_elements=[
                "technical_issue_acknowledgment",
                "error_code_analysis",
                "urgency_recognition",
                "alternative_solution_offer",
                "immediate_escalation_commitment"
            ],
            handoff_information={
                "specialist_type": "Technical Support - Payment Processing",
                "urgency": "High - Payment deadline tomorrow",
                "error_details": "Error 502 - Payment processor connectivity",
                "required_action": "Immediate phone payment processing"
            },
            demo_notes="Shows technical issue recognition and urgent escalation for deadline-sensitive problems"
        ))

        return scenarios

    def _create_emotional_escalation_scenarios(self) -> List[EscalationScenario]:
        """Create emotional distress escalation scenarios"""
        scenarios = []

        # Scenario 3: Homeowner facing foreclosure with emotional distress
        scenarios.append(EscalationScenario(
            scenario_id="escalation_003",
            escalation_type=EscalationType.EMOTIONAL_DISTRESS,
            escalation_trigger=EscalationTrigger.EMOTIONAL_INDICATORS,
            customer_persona="distressed_homeowner",
            property_address="789 Hardship Drive, Houston",
            county="Harris",
            urgency_level="critical",
            conversation_flow=[
                {
                    "user": "I just got a foreclosure notice and I don't know what to do. I lost my job six months ago and I'm behind on everything. I can't lose my house - my kids go to school here!",
                    "ai": "I can hear how stressful and frightening this situation must be for you and your family. Facing foreclosure is one of the most difficult challenges anyone can go through. Please know that there are people who can help you explore all available options to protect your home.",
                    "demo_action": "emotional_validation_and_support"
                },
                {
                    "user": "I don't even know how much I owe or what my options are. Everything seems hopeless.",
                    "ai": "I understand you're feeling overwhelmed right now, and that's completely understandable given what you're facing. You're not alone in this, and it's not hopeless. There are foreclosure prevention programs and assistance options available. I want to connect you immediately with one of our housing counselors who specializes in helping families in exactly your situation.",
                    "demo_action": "hope_restoration_and_specialist_referral"
                },
                {
                    "user": "Will they really be able to help? I feel like I've tried everything.",
                    "ai": "Yes, they absolutely can help. Our housing counselors have helped many families in similar situations find solutions - payment plans, assistance programs, and other options you may not be aware of. I'm connecting you right now with someone who will review your entire situation with compassion and expertise. You're taking the right step by reaching out today.",
                    "demo_action": "reassurance_and_immediate_escalation"
                }
            ],
            escalation_point=2,
            expected_response_elements=[
                "emotional_validation",
                "empathetic_tone",
                "hope_and_reassurance",
                "immediate_specialist_connection",
                "family_situation_acknowledgment"
            ],
            handoff_information={
                "specialist_type": "Housing Counselor - Foreclosure Prevention",
                "urgency": "Critical - Active foreclosure proceedings",
                "emotional_state": "High distress - family with children",
                "required_services": ["Foreclosure prevention counseling", "Financial assistance program evaluation", "Payment plan options"]
            },
            demo_notes="Demonstrates empathetic handling of high-stress situations with immediate human connection"
        ))

        return scenarios

    def _create_multi_jurisdiction_scenarios(self) -> List[EscalationScenario]:
        """Create multi-jurisdiction complexity scenarios"""
        scenarios = []

        # Scenario 4: Property spanning multiple counties/jurisdictions
        scenarios.append(EscalationScenario(
            scenario_id="escalation_004",
            escalation_type=EscalationType.MULTI_JURISDICTION,
            escalation_trigger=EscalationTrigger.COMPLEXITY_THRESHOLD,
            customer_persona="complex_property_owner",
            property_address="1000 County Line Road, Multiple Counties",
            county="Multiple",
            urgency_level="medium",
            conversation_flow=[
                {
                    "user": "My ranch property crosses the line between Williamson and Travis counties. I'm getting different tax bills and conflicting information about exemptions. Who do I pay and how do exemptions work?",
                    "ai": "Properties that span multiple counties can definitely create complex tax situations. Each county will assess and tax the portion of your property within their jurisdiction, and exemption rules may vary between counties. This type of multi-jurisdictional situation requires coordination between different appraisal districts.",
                    "demo_action": "multi_jurisdiction_complexity_acknowledgment"
                },
                {
                    "user": "Williamson County says I need to file exemptions with them, but Travis County says I already have exemptions that should apply to the whole property. This is so confusing!",
                    "ai": "I can understand the confusion - each county operates independently and may have different exemption requirements and applications. Since this involves coordinating between two separate appraisal districts with potentially different rules and systems, this complexity is beyond what I can effectively resolve through our standard process.",
                    "demo_action": "complexity_threshold_recognition"
                },
                {
                    "user": "So what do I do? I don't want to file wrong paperwork or miss deadlines.",
                    "ai": "You're absolutely right to be concerned about proper filing and deadlines. This situation requires someone with expertise in multi-county property taxation who can coordinate with both appraisal districts on your behalf. Let me connect you with our Multi-Jurisdiction Property Specialist who handles exactly these types of complex cross-county situations.",
                    "demo_action": "specialist_escalation_for_complexity"
                }
            ],
            escalation_point=3,
            expected_response_elements=[
                "complexity_acknowledgment",
                "jurisdiction_independence_explanation",
                "confusion_validation",
                "specialist_expertise_requirement",
                "coordination_need_recognition"
            ],
            handoff_information={
                "specialist_type": "Multi-Jurisdiction Property Specialist",
                "urgency": "Medium - Multiple deadlines possible",
                "jurisdictions": ["Williamson County", "Travis County"],
                "required_coordination": "Cross-county exemption application and tax payment coordination"
            },
            demo_notes="Shows recognition of system limitations and appropriate specialist escalation"
        ))

        return scenarios

    def _create_urgent_deadline_scenarios(self) -> List[EscalationScenario]:
        """Create urgent deadline escalation scenarios"""
        scenarios = []

        # Scenario 5: Last-minute appeal filing with complications
        scenarios.append(EscalationScenario(
            scenario_id="escalation_005",
            escalation_type=EscalationType.URGENT_DEADLINE,
            escalation_trigger=EscalationTrigger.TIME_SENSITIVE,
            customer_persona="last_minute_appellant",
            property_address="555 Deadline Drive, San Antonio",
            county="Bexar",
            urgency_level="critical",
            conversation_flow=[
                {
                    "user": "It's 4 PM and the appeal deadline is today at 5 PM. I just found out my property assessment is wrong because they have the wrong square footage. Can I still file an appeal?",
                    "ai": "With just one hour until the deadline, this is definitely a time-critical situation. While it's technically possible to file an appeal, the timing is extremely tight and any complications could result in missing the deadline entirely.",
                    "demo_action": "urgent_deadline_acknowledgment"
                },
                {
                    "user": "I have the correct building plans and a recent appraisal. What do I need to do right now?",
                    "ai": "Those are excellent supporting documents. However, with just 60 minutes left, there's no room for any delays or technical issues. Given the critical timing and the importance of getting this filed correctly before the deadline, I need to immediately connect you with our Appeals Specialist who can expedite your filing and ensure it's submitted properly before 5 PM.",
                    "demo_action": "immediate_escalation_for_deadline"
                },
                {
                    "user": "Yes, please connect me right away!",
                    "ai": "I'm escalating you immediately as our highest priority case. Our Appeals Specialist will call you within the next 5 minutes and will stay on the line with you until your appeal is successfully filed. Please have your property information and supporting documents ready. They will guide you through the fastest filing method to meet today's deadline.",
                    "demo_action": "emergency_escalation_with_commitment"
                }
            ],
            escalation_point=2,
            expected_response_elements=[
                "deadline_urgency_recognition",
                "time_pressure_acknowledgment",
                "immediate_action_commitment",
                "specialist_availability_guarantee",
                "success_assurance"
            ],
            handoff_information={
                "specialist_type": "Appeals Specialist - Emergency Filing",
                "urgency": "Critical - 1 hour to deadline",
                "required_action": "Immediate appeal filing with square footage correction",
                "supporting_documents": ["Building plans", "Recent appraisal"]
            },
            demo_notes="Demonstrates emergency escalation protocols for time-critical situations"
        ))

        return scenarios

    def _create_language_barrier_scenarios(self) -> List[EscalationScenario]:
        """Create language barrier escalation scenarios"""
        scenarios = []

        # Scenario 6: Complex explanation needed in Spanish
        scenarios.append(EscalationScenario(
            scenario_id="escalation_006",
            escalation_type=EscalationType.LANGUAGE_BARRIER,
            escalation_trigger=EscalationTrigger.USER_REQUEST,
            customer_persona="spanish_speaking_homeowner",
            property_address="777 Comunidad Avenue, El Paso",
            county="El Paso",
            urgency_level="medium",
            conversation_flow=[
                {
                    "user": "I need help in Spanish. My English is not good for complicated tax things. ¿Puede ayudarme en español?",
                    "ai": "Sí, entiendo que necesita ayuda en español para asuntos de impuestos de propiedad. While I can provide basic assistance in Spanish, for complex property tax matters, it's important that you receive detailed explanations in your preferred language to ensure complete understanding.",
                    "demo_action": "language_preference_acknowledgment"
                },
                {
                    "user": "I got letter about assessment appeal. Very confusing. Need someone explain everything in Spanish.",
                    "ai": "Entiendo que recibió una carta sobre apelación de evaluación y es confuso. Assessment appeals involve complex processes and deadlines that are very important to understand completely. Para asegurar que reciba toda la información correcta y detallada, I want to connect you with our Spanish-speaking Property Tax Specialist.",
                    "demo_action": "complexity_plus_language_barrier_recognition"
                },
                {
                    "user": "¡Sí, por favor! That would be much better for me.",
                    "ai": "Perfecto. I'm connecting you now with María González, our bilingual Property Tax Specialist who will explain everything about your assessment appeal in Spanish and answer all your questions. She has helped many families in El Paso with similar situations and will make sure you understand all your options and deadlines.",
                    "demo_action": "bilingual_specialist_connection"
                }
            ],
            escalation_point=2,
            expected_response_elements=[
                "language_preference_respect",
                "complexity_acknowledgment",
                "bilingual_specialist_introduction",
                "cultural_competency_demonstration",
                "complete_understanding_priority"
            ],
            handoff_information={
                "specialist_type": "Bilingual Property Tax Specialist",
                "language": "Spanish",
                "urgency": "Medium - Assessment appeal assistance",
                "cultural_considerations": "Ensure complete understanding of complex processes"
            },
            demo_notes="Shows cultural sensitivity and language-appropriate escalation"
        ))

        return scenarios

    def get_scenario_by_id(self, scenario_id: str) -> Optional[EscalationScenario]:
        """Get a specific scenario by ID"""
        for scenario in self.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        return None

    def get_scenarios_by_escalation_type(self, escalation_type: EscalationType) -> List[EscalationScenario]:
        """Get scenarios by escalation type"""
        return [s for s in self.scenarios if s.escalation_type == escalation_type]

    def get_scenarios_by_urgency(self, urgency_level: str) -> List[EscalationScenario]:
        """Get scenarios by urgency level"""
        return [s for s in self.scenarios if s.urgency_level == urgency_level]

    def get_scenarios_by_trigger(self, trigger: EscalationTrigger) -> List[EscalationScenario]:
        """Get scenarios by escalation trigger"""
        return [s for s in self.scenarios if s.escalation_trigger == trigger]

    def get_random_scenario(self) -> EscalationScenario:
        """Get a random scenario for spontaneous demos"""
        return random.choice(self.scenarios)

    def get_escalation_summary(self) -> Dict[str, Any]:
        """Get summary of all escalation scenarios"""
        return {
            "total_scenarios": len(self.scenarios),
            "by_escalation_type": {
                escalation_type.value: len(self.get_scenarios_by_escalation_type(escalation_type))
                for escalation_type in EscalationType
            },
            "by_urgency": {
                urgency: len(self.get_scenarios_by_urgency(urgency))
                for urgency in ["low", "medium", "high", "critical"]
            },
            "by_trigger": {
                trigger.value: len(self.get_scenarios_by_trigger(trigger))
                for trigger in EscalationTrigger
            },
            "average_escalation_point": sum(s.escalation_point for s in self.scenarios) / len(self.scenarios)
        }

    def get_all_scenarios(self) -> List[EscalationScenario]:
        """Get all escalation scenarios"""
        return self.scenarios

# Demo scenario manager
demo_escalation_scenarios = EscalationDemoScenarios()