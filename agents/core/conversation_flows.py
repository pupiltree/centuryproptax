"""
Property Tax Conversation Flows - Standardized conversation logic for Century Property Tax
Implements structured conversation flows for common property tax scenarios with multilingual support
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from config.response_templates import (
    PropertyTaxScenario, Language, get_template,
    detect_language_from_message, get_legal_disclaimer
)

logger = logging.getLogger(__name__)

class ConversationStage(Enum):
    """Conversation stages for property tax interactions"""
    GREETING = "greeting"
    PROBLEM_IDENTIFICATION = "problem_identification"
    INFORMATION_GATHERING = "information_gathering"
    RECOMMENDATION = "recommendation"
    BOOKING_DETAILS = "booking_details"
    PAYMENT_PROCESSING = "payment_processing"
    CONFIRMATION = "confirmation"
    ESCALATION = "escalation"

class PropertyTaxConcern(Enum):
    """Types of property tax concerns"""
    HIGH_ASSESSMENT = "high_assessment"
    MISSING_EXEMPTION = "missing_exemption"
    APPEAL_DEADLINE = "appeal_deadline"
    PAYMENT_DIFFICULTY = "payment_difficulty"
    DOCUMENTATION_HELP = "documentation_help"
    GENERAL_INQUIRY = "general_inquiry"

@dataclass
class ConversationContext:
    """Context information for property tax conversations"""
    session_id: str
    customer_id: str
    language: Language
    current_stage: ConversationStage
    concern_type: Optional[PropertyTaxConcern] = None
    property_type: Optional[str] = None
    county: Optional[str] = None
    assessment_amount: Optional[float] = None
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    pin_code: Optional[str] = None
    preferred_date: Optional[str] = None
    service_type: Optional[str] = None
    payment_method: Optional[str] = None
    address: Optional[str] = None
    collected_info: Dict[str, Any] = None
    previous_messages: List[str] = None

    def __post_init__(self):
        if self.collected_info is None:
            self.collected_info = {}
        if self.previous_messages is None:
            self.previous_messages = []

class PropertyTaxConversationFlow:
    """Manages property tax conversation flows with multilingual support"""

    def __init__(self):
        self.active_conversations: Dict[str, ConversationContext] = {}

    def start_conversation(self, session_id: str, customer_id: str, initial_message: str) -> Tuple[str, ConversationContext]:
        """
        Start a new property tax conversation.

        Args:
            session_id: Unique session identifier
            customer_id: Customer identifier
            initial_message: The customer's first message

        Returns:
            Tuple of (response_message, conversation_context)
        """
        # Detect language from initial message
        language = detect_language_from_message(initial_message)

        # Create conversation context
        context = ConversationContext(
            session_id=session_id,
            customer_id=customer_id,
            language=language,
            current_stage=ConversationStage.GREETING
        )

        # Store the conversation
        self.active_conversations[session_id] = context

        # Generate greeting response
        response = self._generate_greeting_response(context, initial_message)

        return response, context

    def process_message(self, session_id: str, message: str) -> Tuple[str, ConversationContext]:
        """
        Process a message in an ongoing conversation.

        Args:
            session_id: Session identifier
            message: Customer message

        Returns:
            Tuple of (response_message, updated_context)
        """
        context = self.active_conversations.get(session_id)
        if not context:
            # Start new conversation if context not found
            return self.start_conversation(session_id, "unknown", message)

        # Update language if it changes
        detected_language = detect_language_from_message(message)
        if detected_language != Language.ENGLISH:  # Only update if not English (fallback)
            context.language = detected_language

        # Add message to history
        context.previous_messages.append(message)

        # Process based on current stage
        response = self._process_by_stage(context, message)

        return response, context

    def _generate_greeting_response(self, context: ConversationContext, initial_message: str) -> str:
        """Generate an appropriate greeting response."""
        message_lower = initial_message.lower()

        # Check if it's a greeting or direct property tax concern
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'namaste', 'namaskar']):
            # Pure greeting - ask how to help
            template = get_template(PropertyTaxScenario.GREETING, context.language, "initial")
            context.current_stage = ConversationStage.PROBLEM_IDENTIFICATION
        else:
            # Direct concern - acknowledge and move to information gathering
            context.concern_type = self._identify_concern_type(initial_message)
            template = self._get_concern_acknowledgment(context)
            context.current_stage = ConversationStage.INFORMATION_GATHERING

        return template

    def _process_by_stage(self, context: ConversationContext, message: str) -> str:
        """Process message based on current conversation stage."""
        if context.current_stage == ConversationStage.PROBLEM_IDENTIFICATION:
            return self._handle_problem_identification(context, message)
        elif context.current_stage == ConversationStage.INFORMATION_GATHERING:
            return self._handle_information_gathering(context, message)
        elif context.current_stage == ConversationStage.RECOMMENDATION:
            return self._handle_recommendation(context, message)
        elif context.current_stage == ConversationStage.BOOKING_DETAILS:
            return self._handle_booking_details(context, message)
        elif context.current_stage == ConversationStage.PAYMENT_PROCESSING:
            return self._handle_payment_processing(context, message)
        else:
            # Default: try to identify the concern and gather information
            context.current_stage = ConversationStage.INFORMATION_GATHERING
            return self._handle_information_gathering(context, message)

    def _handle_problem_identification(self, context: ConversationContext, message: str) -> str:
        """Handle problem identification stage."""
        context.concern_type = self._identify_concern_type(message)
        context.current_stage = ConversationStage.INFORMATION_GATHERING

        return self._get_concern_acknowledgment(context) + " " + self._get_information_request(context)

    def _handle_information_gathering(self, context: ConversationContext, message: str) -> str:
        """Handle information gathering stage."""
        # Extract information from message
        self._extract_information_from_message(context, message)

        # Check if we have enough information for recommendations
        missing_info = self._get_missing_information(context)

        if not missing_info:
            # We have enough info - move to recommendations
            context.current_stage = ConversationStage.RECOMMENDATION
            return self._generate_recommendations(context)
        else:
            # Still need more info
            return self._request_missing_information(context, missing_info)

    def _handle_recommendation(self, context: ConversationContext, message: str) -> str:
        """Handle recommendation stage."""
        message_lower = message.lower()

        if any(word in message_lower for word in ['yes', 'book', 'schedule', 'proceed', 'confirm']):
            # Customer wants to book - move to booking details
            context.current_stage = ConversationStage.BOOKING_DETAILS
            return self._start_booking_process(context)
        elif any(word in message_lower for word in ['no', 'different', 'other']):
            # Customer wants different options
            return self._provide_alternative_recommendations(context)
        else:
            # Unclear response - ask for clarification
            return self._clarify_recommendation_response(context)

    def _handle_booking_details(self, context: ConversationContext, message: str) -> str:
        """Handle booking details collection."""
        # Extract booking information
        self._extract_booking_information(context, message)

        # Check if we have all required booking details
        missing_booking_info = self._get_missing_booking_information(context)

        if not missing_booking_info:
            # Ready for payment
            context.current_stage = ConversationStage.PAYMENT_PROCESSING
            return self._initiate_payment_process(context)
        else:
            # Still need booking details
            return self._request_missing_booking_information(context, missing_booking_info)

    def _handle_payment_processing(self, context: ConversationContext, message: str) -> str:
        """Handle payment processing stage."""
        message_lower = message.lower()

        if any(word in message_lower for word in ['online', 'card', 'upi', 'net banking']):
            context.payment_method = "online"
            context.current_stage = ConversationStage.CONFIRMATION
            return self._confirm_online_payment(context)
        elif any(word in message_lower for word in ['cash', 'visit', 'person']):
            context.payment_method = "cash"
            context.current_stage = ConversationStage.CONFIRMATION
            return self._confirm_cash_payment(context)
        else:
            # Ask for payment method clarification
            return self._request_payment_method_clarification(context)

    def _identify_concern_type(self, message: str) -> PropertyTaxConcern:
        """Identify the type of property tax concern from message."""
        message_lower = message.lower()

        if any(word in message_lower for word in ['high', 'increased', 'too much', 'expensive']):
            return PropertyTaxConcern.HIGH_ASSESSMENT
        elif any(word in message_lower for word in ['exemption', 'homestead', 'senior', 'disability']):
            return PropertyTaxConcern.MISSING_EXEMPTION
        elif any(word in message_lower for word in ['appeal', 'deadline', 'time limit', 'dispute']):
            return PropertyTaxConcern.APPEAL_DEADLINE
        elif any(word in message_lower for word in ['payment', 'pay', 'installment', 'afford']):
            return PropertyTaxConcern.PAYMENT_DIFFICULTY
        elif any(word in message_lower for word in ['document', 'paperwork', 'form', 'help']):
            return PropertyTaxConcern.DOCUMENTATION_HELP
        else:
            return PropertyTaxConcern.GENERAL_INQUIRY

    def _get_concern_acknowledgment(self, context: ConversationContext) -> str:
        """Get acknowledgment message based on concern type."""
        if context.concern_type == PropertyTaxConcern.HIGH_ASSESSMENT:
            return get_template(PropertyTaxScenario.ASSESSMENT_INQUIRY, context.language, "high_assessment")
        elif context.concern_type == PropertyTaxConcern.MISSING_EXEMPTION:
            return get_template(PropertyTaxScenario.EXEMPTION_QUALIFICATION, context.language, "general")
        elif context.concern_type == PropertyTaxConcern.APPEAL_DEADLINE:
            return get_template(PropertyTaxScenario.APPEAL_PROCESS, context.language, "timeline")
        elif context.concern_type == PropertyTaxConcern.PAYMENT_DIFFICULTY:
            return get_template(PropertyTaxScenario.PAYMENT_OPTIONS, context.language, "installment_plans")
        else:
            if context.language == Language.ENGLISH:
                return "I understand you have questions about property tax. Let me help you find the right solution."
            elif context.language == Language.HINDI:
                return "मैं समझ सकता हूं कि आपके संपत्ति कर के बारे में सवाल हैं। मैं आपको सही समाधान खोजने में मदद करूंगा।"
            elif context.language == Language.BENGALI:
                return "আমি বুঝতে পারি আপনার সম্পত্তি কর নিয়ে প্রশ্ন আছে। আমি আপনাকে সঠিক সমাধান খুঁজে পেতে সাহায্য করব।"
            else:
                return "I understand you have questions about property tax. Let me help you find the right solution."

    def _get_information_request(self, context: ConversationContext) -> str:
        """Get information request based on concern type and language."""
        if context.language == Language.ENGLISH:
            return "To provide the best guidance under Texas property tax law, could you tell me your property type, county, and what specific concerns you have about your assessment?"
        elif context.language == Language.HINDI:
            return "टेक्सास संपत्ति कर कानून के तहत सबसे अच्छी सलाह देने के लिए, क्या आप अपनी संपत्ति का प्रकार, काउंटी और अपने मूल्यांकन के बारे में विशिष्ट चिंताओं के बारे में बता सकते हैं?"
        elif context.language == Language.BENGALI:
            return "টেক্সাস সম্পত্তি কর আইনের অধীনে সেরা নির্দেশনা প্রদানের জন্য, আপনি কি আপনার সম্পত্তির ধরন, কাউন্টি এবং আপনার মূল্যায়ন সম্পর্কে নির্দিষ্ট উদ্বেগের কথা বলতে পারেন?"
        else:
            return "To provide the best guidance under Texas property tax law, could you tell me your property type, county, and what specific concerns you have about your assessment?"

    def _extract_information_from_message(self, context: ConversationContext, message: str):
        """Extract property information from customer message."""
        message_lower = message.lower()

        # Extract property type
        if 'residential' in message_lower or 'home' in message_lower or 'house' in message_lower:
            context.property_type = 'residential'
        elif 'commercial' in message_lower or 'business' in message_lower or 'office' in message_lower:
            context.property_type = 'commercial'
        elif 'land' in message_lower or 'vacant' in message_lower:
            context.property_type = 'land'

        # Extract county information (Texas counties)
        texas_counties = ['harris', 'dallas', 'tarrant', 'bexar', 'travis', 'collin', 'fort bend', 'denton', 'williamson', 'hidalgo']
        for county in texas_counties:
            if county in message_lower:
                context.county = county.title()
                break

        # Extract assessment amount
        import re
        amount_match = re.search(r'\$?([\d,]+)', message)
        if amount_match:
            try:
                context.assessment_amount = float(amount_match.group(1).replace(',', ''))
            except ValueError:
                pass

    def _extract_booking_information(self, context: ConversationContext, message: str):
        """Extract booking information from customer message."""
        message_lower = message.lower()

        # Extract name
        if not context.customer_name:
            # Simple name extraction - in real implementation, use NER
            name_patterns = ['my name is', 'i am', 'this is']
            for pattern in name_patterns:
                if pattern in message_lower:
                    start_idx = message_lower.find(pattern) + len(pattern)
                    potential_name = message[start_idx:start_idx+30].strip().split()[0:3]
                    if potential_name:
                        context.customer_name = ' '.join(potential_name)
                    break

        # Extract phone number
        import re
        phone_match = re.search(r'(\d{10})', message)
        if phone_match:
            context.phone = phone_match.group(1)

        # Extract PIN code
        pin_match = re.search(r'\b(\d{6})\b', message)
        if pin_match:
            context.pin_code = pin_match.group(1)

        # Extract service preference
        if any(word in message_lower for word in ['visit', 'home', 'property', 'come to']):
            context.service_type = 'property_visit'
        elif any(word in message_lower for word in ['office', 'consultation', 'visit you', 'come to office']):
            context.service_type = 'office_consultation'

    def _get_missing_information(self, context: ConversationContext) -> List[str]:
        """Get list of missing information needed for recommendations."""
        missing = []

        if not context.property_type:
            missing.append('property_type')
        if not context.county:
            missing.append('county')
        if context.concern_type == PropertyTaxConcern.HIGH_ASSESSMENT and not context.assessment_amount:
            missing.append('assessment_amount')

        return missing

    def _get_missing_booking_information(self, context: ConversationContext) -> List[str]:
        """Get list of missing booking information."""
        missing = []

        if not context.customer_name:
            missing.append('customer_name')
        if not context.phone:
            missing.append('phone')
        if not context.pin_code:
            missing.append('pin_code')
        if not context.preferred_date:
            missing.append('preferred_date')
        if not context.service_type:
            missing.append('service_type')
        if context.service_type == 'property_visit' and not context.address:
            missing.append('address')

        return missing

    def _request_missing_information(self, context: ConversationContext, missing_info: List[str]) -> str:
        """Request missing information from customer."""
        if context.language == Language.ENGLISH:
            if 'property_type' in missing_info:
                return "To provide accurate recommendations, I need to know what type of property this is - residential home, commercial building, or vacant land?"
            elif 'county' in missing_info:
                return "Which Texas county is your property located in? This helps me provide county-specific guidance."
            elif 'assessment_amount' in missing_info:
                return "What is the current assessed value shown on your property tax notice? This helps me understand if the assessment seems appropriate."
        elif context.language == Language.HINDI:
            if 'property_type' in missing_info:
                return "सटीक सिफारिशें प्रदान करने के लिए, मुझे यह जानना होगा कि यह किस प्रकार की संपत्ति है - आवासीय घर, वाणिज्यिक भवन, या खाली जमीन?"
            elif 'county' in missing_info:
                return "आपकी संपत्ति टेक्सास के किस काउंटी में स्थित है? यह मुझे काउंटी-विशिष्ट मार्गदर्शन प्रदान करने में मदद करता है।"
        elif context.language == Language.BENGALI:
            if 'property_type' in missing_info:
                return "সঠিক সুপারিশ প্রদানের জন্য, আমার জানা দরকার এটি কী ধরনের সম্পত্তি - আবাসিক বাড়ি, বাণিজ্যিক ভবন, বা খালি জমি?"
            elif 'county' in missing_info:
                return "আপনার সম্পত্তি টেক্সাসের কোন কাউন্টিতে অবস্থিত? এটি আমাকে কাউন্টি-নির্দিষ্ট নির্দেশনা প্রদান করতে সাহায্য করে।"

        return "Could you provide a bit more information about your property situation?"

    def _generate_recommendations(self, context: ConversationContext) -> str:
        """Generate property tax recommendations based on gathered information."""
        recommendations = []

        if context.concern_type == PropertyTaxConcern.HIGH_ASSESSMENT:
            recommendations.append("Property Tax Assessment Review")
            recommendations.append("Appeal Preparation Consultation")
        elif context.concern_type == PropertyTaxConcern.MISSING_EXEMPTION:
            recommendations.append("Exemption Analysis and Application")
        elif context.concern_type == PropertyTaxConcern.APPEAL_DEADLINE:
            recommendations.append("Urgent Appeal Filing Assistance")
        else:
            recommendations.append("Comprehensive Property Tax Analysis")

        # Add legal disclaimer
        disclaimer = get_legal_disclaimer(context.language, "assessment_guidance")

        if context.language == Language.ENGLISH:
            response = f"Based on your {context.property_type} property in {context.county} County, I recommend these services:\n\n"
            response += "\n".join(f"• {rec}" for rec in recommendations)
            response += f"\n\nWould you like to book these assessments?\n\n{disclaimer}"
        elif context.language == Language.HINDI:
            response = f"{context.county} काउंटी में आपकी {context.property_type} संपत्ति के आधार पर, मैं इन सेवाओं की सिफारिश करता हूं:\n\n"
            response += "\n".join(f"• {rec}" for rec in recommendations)
            response += f"\n\nक्या आप इन मूल्यांकनों को बुक करना चाहेंगे?\n\n{disclaimer}"
        elif context.language == Language.BENGALI:
            response = f"{context.county} কাউন্টিতে আপনার {context.property_type} সম্পত্তির ভিত্তিতে, আমি এই সেবাগুলির সুপারিশ করি:\n\n"
            response += "\n".join(f"• {rec}" for rec in recommendations)
            response += f"\n\nআপনি কি এই মূল্যায়নগুলি বুক করতে চান?\n\n{disclaimer}"

        return response

    def _start_booking_process(self, context: ConversationContext) -> str:
        """Start the booking process."""
        if context.language == Language.ENGLISH:
            return "Perfect! Let's book your property tax assessment. I'll need a few details:\n\n• Your full name and phone number\n• Your property PIN code and preferred date\n• Would you prefer property visit for inspection or office consultation?\n\nLet's start - what's your full name?"
        elif context.language == Language.HINDI:
            return "बहुत बढ़िया! आइए आपके संपत्ति कर मूल्यांकन को बुक करते हैं। मुझे कुछ विवरण चाहिए:\n\n• आपका पूरा नाम और फोन नंबर\n• आपका संपत्ति PIN कोड और पसंदीदा तारीख\n• क्या आप निरीक्षण के लिए संपत्ति यात्रा या कार्यालय परामर्श पसंद करेंगे?\n\nशुरू करते हैं - आपका पूरा नाम क्या है?"
        elif context.language == Language.BENGALI:
            return "দুর্দান্ত! আসুন আপনার সম্পত্তি কর মূল্যায়ন বুক করি। আমার কিছু বিবরণ দরকার:\n\n• আপনার পূর্ণ নাম এবং ফোন নম্বর\n• আপনার সম্পত্তি PIN কোড এবং পছন্দের তারিখ\n• আপনি কি পরিদর্শনের জন্য সম্পত্তি পরিদর্শন বা অফিস পরামর্শ পছন্দ করবেন?\n\nশুরু করি - আপনার পূর্ণ নাম কী?"

        return "Perfect! Let's book your property tax assessment. What's your full name?"

    def get_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for a session."""
        return self.active_conversations.get(session_id)

    def end_conversation(self, session_id: str):
        """End and clean up a conversation."""
        self.active_conversations.pop(session_id, None)

# Global conversation flow manager
_conversation_flow_manager = None

def get_conversation_flow_manager() -> PropertyTaxConversationFlow:
    """Get or create the global conversation flow manager."""
    global _conversation_flow_manager
    if _conversation_flow_manager is None:
        _conversation_flow_manager = PropertyTaxConversationFlow()
        logger.info("🔄 Created property tax conversation flow manager")
    return _conversation_flow_manager

# Utility functions for easy integration
def start_property_tax_conversation(session_id: str, customer_id: str, message: str) -> Tuple[str, Dict[str, Any]]:
    """
    Start a new property tax conversation.

    Args:
        session_id: Unique session identifier
        customer_id: Customer identifier
        message: Initial customer message

    Returns:
        Tuple of (response_message, conversation_context_dict)
    """
    flow_manager = get_conversation_flow_manager()
    response, context = flow_manager.start_conversation(session_id, customer_id, message)

    return response, {
        'session_id': context.session_id,
        'customer_id': context.customer_id,
        'language': context.language.value,
        'current_stage': context.current_stage.value,
        'concern_type': context.concern_type.value if context.concern_type else None,
        'property_type': context.property_type,
        'county': context.county,
        'collected_info': context.collected_info
    }

def process_property_tax_message(session_id: str, message: str) -> Tuple[str, Dict[str, Any]]:
    """
    Process a message in an ongoing property tax conversation.

    Args:
        session_id: Session identifier
        message: Customer message

    Returns:
        Tuple of (response_message, conversation_context_dict)
    """
    flow_manager = get_conversation_flow_manager()
    response, context = flow_manager.process_message(session_id, message)

    return response, {
        'session_id': context.session_id,
        'customer_id': context.customer_id,
        'language': context.language.value,
        'current_stage': context.current_stage.value,
        'concern_type': context.concern_type.value if context.concern_type else None,
        'property_type': context.property_type,
        'county': context.county,
        'collected_info': context.collected_info
    }

# Export key classes and functions
__all__ = [
    'ConversationStage',
    'PropertyTaxConcern',
    'ConversationContext',
    'PropertyTaxConversationFlow',
    'get_conversation_flow_manager',
    'start_property_tax_conversation',
    'process_property_tax_message'
]