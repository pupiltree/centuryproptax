"""
Property Tax AI Guardrails - Domain-specific safety measures and response validation
Implements comprehensive guardrails for property tax AI interactions to ensure appropriate boundaries
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass

from config.ai_configuration import (
    PropertyTaxDomain, ConfidenceLevel, get_ai_config,
    validate_legal_boundaries
)

logger = logging.getLogger(__name__)

class GuardrailViolationType(Enum):
    """Types of guardrail violations"""
    LEGAL_ADVICE_REQUEST = "legal_advice_request"
    GUARANTEE_REQUEST = "guarantee_request"
    UNAUTHORIZED_REPRESENTATION = "unauthorized_representation"
    FINANCIAL_ADVICE_REQUEST = "financial_advice_request"
    CONFIDENTIAL_INFO_SHARING = "confidential_info_sharing"
    INAPPROPRIATE_URGENCY = "inappropriate_urgency"
    OUT_OF_SCOPE_REQUEST = "out_of_scope_request"
    HARMFUL_CONTENT = "harmful_content"
    PRIVACY_VIOLATION = "privacy_violation"

class ResponseAction(Enum):
    """Actions to take based on guardrail analysis"""
    ALLOW = "allow"
    MODIFY = "modify"
    ESCALATE = "escalate"
    BLOCK = "block"
    REDIRECT = "redirect"

@dataclass
class GuardrailResult:
    """Result of guardrail analysis"""
    action: ResponseAction
    violations: List[GuardrailViolationType]
    confidence: float
    recommended_response: Optional[str] = None
    escalation_reason: Optional[str] = None
    modifications_needed: List[str] = None

    def __post_init__(self):
        if self.modifications_needed is None:
            self.modifications_needed = []

class PropertyTaxGuardrails:
    """Comprehensive guardrail system for property tax AI interactions"""

    def __init__(self):
        self.ai_config = get_ai_config()

        # Patterns for detecting various violation types
        self.violation_patterns = {
            GuardrailViolationType.LEGAL_ADVICE_REQUEST: [
                r'\b(should i|what should i do|legal advice|legally speaking|is it legal)\b',
                r'\b(sue|lawsuit|litigation|court case|legal action)\b',
                r'\b(lawyer|attorney|legal counsel|legal representation)\b',
                r'\b(my rights|legal rights|what are my options legally)\b'
            ],

            GuardrailViolationType.GUARANTEE_REQUEST: [
                r'\b(guarantee|promise|ensure|certain|definitely will)\b',
                r'\b(will i win|will this work|guaranteed success)\b',
                r'\b(100% sure|absolutely certain|no doubt)\b'
            ],

            GuardrailViolationType.UNAUTHORIZED_REPRESENTATION: [
                r'\b(represent me|speak for me|file for me|act on my behalf)\b',
                r'\b(be my lawyer|be my agent|be my representative)\b',
                r'\b(sign documents|authorize|power of attorney)\b'
            ],

            GuardrailViolationType.FINANCIAL_ADVICE_REQUEST: [
                r'\b(investment advice|financial planning|tax shelter)\b',
                r'\b(should i invest|financial strategy|portfolio)\b',
                r'\b(mortgage advice|refinance|credit score)\b'
            ],

            GuardrailViolationType.CONFIDENTIAL_INFO_SHARING: [
                r'\b(ssn|social security|bank account|credit card)\b',
                r'\b(password|pin|personal identification)\b',
                r'\b(confidential|private|classified)\b'
            ],

            GuardrailViolationType.OUT_OF_SCOPE_REQUEST: [
                r'\b(medical|health|diagnosis|treatment)\b',
                r'\b(immigration|visa|citizenship|deportation)\b',
                r'\b(criminal|arrest|police|jail)\b',
                r'\b(divorce|child custody|family law)\b'
            ],

            GuardrailViolationType.HARMFUL_CONTENT: [
                r'\b(violence|harm|threat|suicide|kill)\b',
                r'\b(illegal|fraud|scam|cheat|lie)\b',
                r'\b(discrimination|racist|sexist)\b'
            ]
        }

        # Safe response templates by violation type
        self.safe_responses = {
            GuardrailViolationType.LEGAL_ADVICE_REQUEST: {
                "en": "I can provide general information about property tax procedures, but I cannot give specific legal advice. For legal matters, I recommend consulting with a licensed property tax attorney or consultant.",
                "hi": "मैं संपत्ति कर प्रक्रियाओं के बारे में सामान्य जानकारी प्रदान कर सकता हूं, लेकिन मैं विशिष्ट कानूनी सलाह नहीं दे सकता। कानूनी मामलों के लिए, मैं लाइसेंस प्राप्त संपत्ति कर वकील या सलाहकार से परामर्श की सिफारिश करता हूं।",
                "bn": "আমি সম্পত্তি কর পদ্ধতি সম্পর্কে সাধারণ তথ্য প্রদান করতে পারি, কিন্তু আমি নির্দিষ্ট আইনি পরামর্শ দিতে পারি না। আইনি বিষয়ের জন্য, আমি লাইসেন্সপ্রাপ্ত সম্পত্তি কর আইনজীবী বা পরামর্শদাতার সাথে পরামর্শের সুপারিশ করি।"
            },

            GuardrailViolationType.GUARANTEE_REQUEST: {
                "en": "I cannot guarantee specific outcomes for property tax matters, as each case is unique and depends on many factors. I can help you understand the process and your options, but results will depend on your specific circumstances.",
                "hi": "मैं संपत्ति कर मामलों के लिए विशिष्ट परिणामों की गारंटी नहीं दे सकता, क्योंकि हर मामला अनोखा है और कई कारकों पर निर्भर करता है। मैं आपको प्रक्रिया और आपके विकल्पों को समझने में मदद कर सकता हूं, लेकिन परिणाम आपकी विशिष्ट परिस्थितियों पर निर्भर करेंगे।",
                "bn": "আমি সম্পত্তি কর বিষয়ের জন্য নির্দিষ্ট ফলাফলের গ্যারান্টি দিতে পারি না, কারণ প্রতিটি ক্ষেত্রে অনন্য এবং অনেক কারণের উপর নির্ভর করে। আমি আপনাকে প্রক্রিয়া এবং আপনার বিকল্পগুলি বুঝতে সাহায্য করতে পারি, কিন্তু ফলাফল আপনার নির্দিষ্ট পরিস্থিতিতে নির্ভর করবে।"
            },

            GuardrailViolationType.UNAUTHORIZED_REPRESENTATION: {
                "en": "I cannot represent you in legal proceedings or act on your behalf. I can provide guidance and information, but you'll need to take action yourself or hire a qualified professional for representation.",
                "hi": "मैं कानूनी कार्यवाही में आपका प्रतिनिधित्व नहीं कर सकता या आपकी ओर से कार्य नहीं कर सकता। मैं मार्गदर्शन और जानकारी प्रदान कर सकता हूं, लेकिन आपको स्वयं कार्रवाई करनी होगी या प्रतिनिधित्व के लिए एक योग्य पेशेवर को नियुक्त करना होगा।",
                "bn": "আমি আইনি কার্যক্রমে আপনার প্রতিনিধিত্व করতে পারি না বা আপনার পক্ষে কাজ করতে পারি না। আমি নির্দেশনা এবং তথ্য প্রদান করতে পারি, কিন্তু আপনাকে নিজেই পদক্ষেপ নিতে হবে বা প্রতিনিধিত্বের জন্য একজন যোগ্য পেশাদার নিয়োগ করতে হবে।"
            },

            GuardrailViolationType.OUT_OF_SCOPE_REQUEST: {
                "en": "I specialize in property tax matters. For questions about other topics, I recommend consulting with appropriate specialists or professionals in those fields.",
                "hi": "मैं संपत्ति कर मामलों में विशेषज्ञ हूं। अन्य विषयों के बारे में प्रश्नों के लिए, मैं उन क्षेत्रों में उपयुक्त विशेषज्ञों या पेशेवरों से परामर्श की सिफारिश करता हूं।",
                "bn": "আমি সম্পত্তি কর বিষয়ে বিশেষজ্ঞ। অন্যান্য বিষয়ে প্রশ্নের জন্য, আমি সেই ক্ষেত্রে উপযুক্ত বিশেষজ্ঞ বা পেশাদারদের সাথে পরামর্শের সুপারিশ করি।"
            }
        }

    def analyze_user_input(self, user_message: str, domain: PropertyTaxDomain, language: str = "en") -> GuardrailResult:
        """
        Analyze user input for guardrail violations.

        Args:
            user_message: The user's message
            domain: Property tax domain category
            language: User's language preference

        Returns:
            GuardrailResult with analysis and recommended actions
        """
        violations = []
        confidence = 1.0
        message_lower = user_message.lower()

        # Check for each violation type
        for violation_type, patterns in self.violation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    violations.append(violation_type)
                    break

        # Check legal boundaries from AI config
        within_boundaries, boundary_violations = validate_legal_boundaries(domain, user_message)
        if not within_boundaries:
            violations.append(GuardrailViolationType.LEGAL_ADVICE_REQUEST)

        # Determine action based on violations
        if not violations:
            return GuardrailResult(
                action=ResponseAction.ALLOW,
                violations=[],
                confidence=confidence
            )

        # Handle specific violation types
        if GuardrailViolationType.HARMFUL_CONTENT in violations:
            return GuardrailResult(
                action=ResponseAction.BLOCK,
                violations=violations,
                confidence=confidence,
                recommended_response="I cannot assist with that request. Let me help you with property tax questions instead."
            )

        if GuardrailViolationType.OUT_OF_SCOPE_REQUEST in violations:
            return GuardrailResult(
                action=ResponseAction.REDIRECT,
                violations=violations,
                confidence=confidence,
                recommended_response=self.safe_responses[GuardrailViolationType.OUT_OF_SCOPE_REQUEST].get(language, self.safe_responses[GuardrailViolationType.OUT_OF_SCOPE_REQUEST]["en"])
            )

        # For legal advice or representation requests
        if any(v in violations for v in [GuardrailViolationType.LEGAL_ADVICE_REQUEST, GuardrailViolationType.UNAUTHORIZED_REPRESENTATION]):
            return GuardrailResult(
                action=ResponseAction.ESCALATE,
                violations=violations,
                confidence=confidence,
                escalation_reason="User requesting legal advice or representation beyond scope",
                recommended_response=self._get_safe_response(violations[0], language)
            )

        # For guarantee requests - modify response
        if GuardrailViolationType.GUARANTEE_REQUEST in violations:
            return GuardrailResult(
                action=ResponseAction.MODIFY,
                violations=violations,
                confidence=confidence,
                modifications_needed=["Add disclaimer about no guarantees", "Focus on process explanation"],
                recommended_response=self.safe_responses[GuardrailViolationType.GUARANTEE_REQUEST].get(language, self.safe_responses[GuardrailViolationType.GUARANTEE_REQUEST]["en"])
            )

        # Default: modify response with appropriate disclaimers
        return GuardrailResult(
            action=ResponseAction.MODIFY,
            violations=violations,
            confidence=confidence,
            modifications_needed=["Add appropriate disclaimers", "Clarify limitations"],
            recommended_response=self._get_safe_response(violations[0], language)
        )

    def analyze_ai_response(self, response: str, domain: PropertyTaxDomain, user_message: str) -> GuardrailResult:
        """
        Analyze AI response for potential issues.

        Args:
            response: The AI's generated response
            domain: Property tax domain category
            user_message: Original user message for context

        Returns:
            GuardrailResult with analysis and recommended modifications
        """
        violations = []
        response_lower = response.lower()

        # Check for inappropriate guarantees in response
        guarantee_patterns = [
            r'\b(guarantee|promise|will definitely|100% certain)\b',
            r'\b(you will win|this will work|assured success)\b'
        ]

        for pattern in guarantee_patterns:
            if re.search(pattern, response_lower):
                violations.append(GuardrailViolationType.GUARANTEE_REQUEST)
                break

        # Check for legal advice language
        legal_advice_patterns = [
            r'\b(you should legally|my legal recommendation|legally you must)\b',
            r'\b(as your attorney|legal counsel advises|from a legal standpoint)\b'
        ]

        for pattern in legal_advice_patterns:
            if re.search(pattern, response_lower):
                violations.append(GuardrailViolationType.LEGAL_ADVICE_REQUEST)
                break

        # Check response length against domain limits
        domain_config = self.ai_config.get_domain_config(domain)
        if len(response) > domain_config.max_response_length:
            modifications_needed = ["Shorten response to meet domain limits"]
        else:
            modifications_needed = []

        # Check if disclaimer is needed but missing
        if domain_config.requires_disclaimer and not self._has_disclaimer(response):
            modifications_needed.append("Add required legal disclaimer")

        if violations or modifications_needed:
            return GuardrailResult(
                action=ResponseAction.MODIFY,
                violations=violations,
                confidence=0.8,
                modifications_needed=modifications_needed
            )

        return GuardrailResult(
            action=ResponseAction.ALLOW,
            violations=[],
            confidence=1.0
        )

    def apply_response_modifications(self, response: str, guardrail_result: GuardrailResult, domain: PropertyTaxDomain, language: str = "en") -> str:
        """
        Apply necessary modifications to AI response based on guardrail analysis.

        Args:
            response: Original AI response
            guardrail_result: Result of guardrail analysis
            domain: Property tax domain
            language: User's language preference

        Returns:
            Modified response with appropriate guardrails applied
        """
        if guardrail_result.action == ResponseAction.ALLOW:
            return response

        if guardrail_result.action == ResponseAction.BLOCK:
            return guardrail_result.recommended_response or "I cannot assist with that request."

        if guardrail_result.action in [ResponseAction.REDIRECT, ResponseAction.ESCALATE]:
            if guardrail_result.recommended_response:
                return guardrail_result.recommended_response
            return response

        # Apply modifications
        modified_response = response

        if "Add disclaimer about no guarantees" in guardrail_result.modifications_needed:
            modified_response = self._remove_guarantee_language(modified_response)

        if "Add appropriate disclaimers" in guardrail_result.modifications_needed:
            disclaimer = self.ai_config.get_legal_disclaimer(domain, language)
            modified_response = f"{modified_response}\n\n{disclaimer}"

        if "Add required legal disclaimer" in guardrail_result.modifications_needed:
            disclaimer = self.ai_config.get_legal_disclaimer(domain, language)
            modified_response = f"{modified_response}\n\n{disclaimer}"

        if "Shorten response to meet domain limits" in guardrail_result.modifications_needed:
            domain_config = self.ai_config.get_domain_config(domain)
            max_length = domain_config.max_response_length - 200  # Reserve space for disclaimers
            if len(modified_response) > max_length:
                modified_response = modified_response[:max_length] + "..."

        if "Clarify limitations" in guardrail_result.modifications_needed:
            modified_response = self._add_limitation_clarifications(modified_response, language)

        return modified_response

    def _get_safe_response(self, violation_type: GuardrailViolationType, language: str) -> str:
        """Get safe response for specific violation type."""
        safe_response = self.safe_responses.get(violation_type, {})
        return safe_response.get(language, safe_response.get("en", "I can help you with property tax questions within my scope of service."))

    def _has_disclaimer(self, response: str) -> bool:
        """Check if response already contains a disclaimer."""
        disclaimer_indicators = ["disclaimer", "not legal advice", "consult", "attorney", "professional"]
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in disclaimer_indicators)

    def _remove_guarantee_language(self, response: str) -> str:
        """Remove or soften guarantee language in response."""
        # Replace absolute language with more appropriate alternatives
        replacements = {
            r'\bguarantee\b': 'may help',
            r'\bpromise\b': 'expect',
            r'\bwill definitely\b': 'typically',
            r'\b100% certain\b': 'likely',
            r'\bassured\b': 'possible'
        }

        modified = response
        for pattern, replacement in replacements.items():
            modified = re.sub(pattern, replacement, modified, flags=re.IGNORECASE)

        return modified

    def _add_limitation_clarifications(self, response: str, language: str) -> str:
        """Add clarifications about service limitations."""
        if language == "hi":
            clarification = "\n\nनोट: यह सामान्य मार्गदर्शन है और विशिष्ट कानूनी सलाह नहीं है।"
        elif language == "bn":
            clarification = "\n\nনোট: এটি সাধারণ নির্দেশনা এবং নির্দিষ্ট আইনি পরামর্শ নয়।"
        else:
            clarification = "\n\nNote: This is general guidance and not specific legal advice."

        return response + clarification

    def check_escalation_needed(self, user_message: str, domain: PropertyTaxDomain, confidence: float) -> Tuple[bool, str]:
        """
        Check if conversation should be escalated to human agent.

        Args:
            user_message: User's message
            domain: Property tax domain
            confidence: AI confidence in handling the request

        Returns:
            Tuple of (should_escalate, reason)
        """
        # Check AI config escalation rules
        if self.ai_config.should_escalate(domain, user_message, confidence):
            return True, "Low confidence or complex query requiring human expertise"

        # Check guardrail violations that require escalation
        guardrail_result = self.analyze_user_input(user_message, domain)
        if guardrail_result.action == ResponseAction.ESCALATE:
            return True, guardrail_result.escalation_reason or "User request requires human assistance"

        # Check for urgent deadline situations
        urgent_patterns = [
            r'\b(deadline|urgent|emergency|today|tomorrow|asap)\b',
            r'\b(due today|due tomorrow|expires|time sensitive)\b'
        ]

        message_lower = user_message.lower()
        for pattern in urgent_patterns:
            if re.search(pattern, message_lower):
                return True, "Time-sensitive request requiring immediate human attention"

        return False, ""

# Global guardrails instance
_guardrails = None

def get_guardrails() -> PropertyTaxGuardrails:
    """Get or create the global guardrails instance."""
    global _guardrails
    if _guardrails is None:
        _guardrails = PropertyTaxGuardrails()
        logger.info("🛡️ Created property tax guardrails system")
    return _guardrails

# Utility functions for easy integration
def validate_user_input(user_message: str, domain: PropertyTaxDomain, language: str = "en") -> GuardrailResult:
    """Validate user input against guardrails."""
    guardrails = get_guardrails()
    return guardrails.analyze_user_input(user_message, domain, language)

def validate_ai_response(response: str, domain: PropertyTaxDomain, user_message: str) -> GuardrailResult:
    """Validate AI response against guardrails."""
    guardrails = get_guardrails()
    return guardrails.analyze_ai_response(response, domain, user_message)

def apply_guardrails(response: str, domain: PropertyTaxDomain, user_message: str, language: str = "en") -> str:
    """Apply guardrails to AI response."""
    guardrails = get_guardrails()

    # Analyze the response
    guardrail_result = guardrails.analyze_ai_response(response, domain, user_message)

    # Apply modifications if needed
    return guardrails.apply_response_modifications(response, guardrail_result, domain, language)

def should_escalate_to_human(user_message: str, domain: PropertyTaxDomain, confidence: float = 1.0) -> Tuple[bool, str]:
    """Check if conversation should be escalated to human agent."""
    guardrails = get_guardrails()
    return guardrails.check_escalation_needed(user_message, domain, confidence)

# Export key classes and functions
__all__ = [
    'GuardrailViolationType',
    'ResponseAction',
    'GuardrailResult',
    'PropertyTaxGuardrails',
    'get_guardrails',
    'validate_user_input',
    'validate_ai_response',
    'apply_guardrails',
    'should_escalate_to_human'
]