"""
AI Configuration for Century Property Tax - Centralized settings and domain-specific configuration
Controls AI behavior, model selection, and domain-specific parameters for property tax operations
"""

import os
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class AIModel(Enum):
    """Available AI models for different tasks"""
    GEMINI_FLASH = "gemini-2.5-flash"
    GEMINI_PRO = "gemini-2.5-pro"

class PropertyTaxDomain(Enum):
    """Property tax domain categories"""
    ASSESSMENT = "assessment"
    APPEAL = "appeal"
    EXEMPTION = "exemption"
    PAYMENT = "payment"
    DOCUMENTATION = "documentation"
    GENERAL_INQUIRY = "general_inquiry"

class ConfidenceLevel(Enum):
    """AI confidence levels for responses"""
    HIGH = "high"          # 90%+ confidence
    MEDIUM = "medium"      # 70-89% confidence
    LOW = "low"            # 50-69% confidence
    UNCERTAIN = "uncertain" # <50% confidence

@dataclass
class AIModelConfig:
    """Configuration for AI models"""
    model_name: str
    temperature: float
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None

@dataclass
class DomainConfig:
    """Domain-specific configuration"""
    domain: PropertyTaxDomain
    requires_disclaimer: bool
    legal_boundaries: List[str]
    recommended_escalation_triggers: List[str]
    confidence_threshold: float
    max_response_length: int

# AI Model Configurations for different use cases
AI_MODEL_CONFIGS = {
    # Text conversations - balanced speed and accuracy
    "text_conversation": AIModelConfig(
        model_name=AIModel.GEMINI_FLASH.value,
        temperature=0.1,  # Conservative for property tax accuracy
        max_tokens=2000,
        top_p=0.8
    ),

    # Document analysis - high accuracy needed
    "document_analysis": AIModelConfig(
        model_name=AIModel.GEMINI_PRO.value,
        temperature=0.05,  # Very conservative for document accuracy
        max_tokens=4000,
        top_p=0.7
    ),


    # Property tax analysis - domain expertise
    "property_tax_analysis": AIModelConfig(
        model_name=AIModel.GEMINI_PRO.value,
        temperature=0.1,
        max_tokens=3000,
        top_p=0.8
    ),

    # Emergency/urgent cases - balanced response
    "urgent_response": AIModelConfig(
        model_name=AIModel.GEMINI_FLASH.value,
        temperature=0.15,
        max_tokens=1000,
        top_p=0.9
    )
}

# Domain-specific configurations with legal boundaries
DOMAIN_CONFIGS = {
    PropertyTaxDomain.ASSESSMENT: DomainConfig(
        domain=PropertyTaxDomain.ASSESSMENT,
        requires_disclaimer=True,
        legal_boundaries=[
            "Cannot guarantee specific assessment outcomes",
            "Cannot provide official property valuations",
            "Cannot represent clients in formal proceedings",
            "Cannot interpret complex legal statutes without professional review"
        ],
        recommended_escalation_triggers=[
            "requests for guaranteed assessment results",
            "complex legal interpretation questions",
            "formal representation requests",
            "litigation-related inquiries"
        ],
        confidence_threshold=0.75,
        max_response_length=2500
    ),

    PropertyTaxDomain.APPEAL: DomainConfig(
        domain=PropertyTaxDomain.APPEAL,
        requires_disclaimer=True,
        legal_boundaries=[
            "Cannot guarantee appeal success",
            "Cannot provide legal representation",
            "Cannot file appeals on behalf of clients",
            "Cannot give specific legal advice for complex cases"
        ],
        recommended_escalation_triggers=[
            "requests for legal representation",
            "complex appeal strategy questions",
            "deadline-critical situations",
            "requests for guaranteed outcomes"
        ],
        confidence_threshold=0.8,
        max_response_length=3000
    ),

    PropertyTaxDomain.EXEMPTION: DomainConfig(
        domain=PropertyTaxDomain.EXEMPTION,
        requires_disclaimer=False,  # Exemption info is more factual
        legal_boundaries=[
            "Cannot guarantee exemption approval",
            "Cannot complete exemption applications",
            "Cannot provide legal advice on complex eligibility"
        ],
        recommended_escalation_triggers=[
            "complex eligibility questions",
            "legal disputes over exemptions",
            "deadline-critical applications"
        ],
        confidence_threshold=0.7,
        max_response_length=2000
    ),

    PropertyTaxDomain.PAYMENT: DomainConfig(
        domain=PropertyTaxDomain.PAYMENT,
        requires_disclaimer=False,
        legal_boundaries=[
            "Cannot process actual payments",
            "Cannot provide financial advice",
            "Cannot guarantee payment plan approval"
        ],
        recommended_escalation_triggers=[
            "financial hardship cases",
            "complex payment arrangements",
            "legal collection issues"
        ],
        confidence_threshold=0.75,
        max_response_length=1500
    ),

    PropertyTaxDomain.DOCUMENTATION: DomainConfig(
        domain=PropertyTaxDomain.DOCUMENTATION,
        requires_disclaimer=False,
        legal_boundaries=[
            "Cannot complete legal documents",
            "Cannot provide legal document review",
            "Cannot guarantee document accuracy"
        ],
        recommended_escalation_triggers=[
            "complex legal documents",
            "formal legal filings",
            "document authenticity questions"
        ],
        confidence_threshold=0.7,
        max_response_length=2000
    ),

    PropertyTaxDomain.GENERAL_INQUIRY: DomainConfig(
        domain=PropertyTaxDomain.GENERAL_INQUIRY,
        requires_disclaimer=True,
        legal_boundaries=[
            "Cannot provide specific legal advice",
            "Cannot guarantee accuracy of general information",
            "Cannot replace professional consultation"
        ],
        recommended_escalation_triggers=[
            "complex legal questions",
            "case-specific advice requests",
            "urgent deadline situations"
        ],
        confidence_threshold=0.65,
        max_response_length=2000
    )
}

# Texas Property Tax Knowledge Base Configuration
TEXAS_PROPERTY_TAX_CONFIG = {
    # Key deadlines and dates
    "important_dates": {
        "assessment_date": "January 1",
        "exemption_deadline": "April 30",
        "informal_review_deadline": "May 15",
        "arb_hearing_deadline": "July 20",
        "payment_deadline": "January 31",
        "delinquency_date": "February 1"
    },

    # Exemption amounts and criteria
    "exemptions": {
        "homestead_minimum": 40000,
        "senior_age_requirement": 65,
        "disability_threshold_requirements": True,
        "veteran_disability_ratings": [10, 30, 50, 70, 100]
    },

    # Common assessment ranges by property type
    "assessment_ranges": {
        "residential": {"min": 50000, "max": 2000000},
        "commercial": {"min": 100000, "max": 10000000},
        "agricultural": {"min": 1000, "max": 500000},
        "industrial": {"min": 500000, "max": 50000000}
    },

    # County-specific information
    "major_counties": [
        "Harris", "Dallas", "Tarrant", "Bexar", "Travis", "Collin",
        "Fort Bend", "Denton", "Williamson", "Hidalgo"
    ]
}

# Legal disclaimer templates by domain
LEGAL_DISCLAIMERS = {
    PropertyTaxDomain.ASSESSMENT: {
        "en": "This professional assessment will help you understand your property tax situation, but for complex legal matters involving appeals or disputes, we may recommend consultation with a property tax attorney.",
        "hi": "यह पेशेवर मूल्यांकन आपको अपनी संपत्ति कर स्थिति को समझने में मदद करेगा, लेकिन अपील या विवादों से जुड़े जटिल कानूनी मामलों के लिए, हम संपत्ति कर वकील से सलाह की सिफारिश कर सकते हैं।",
        "bn": "এই পেশাদার মূল্যায়ন আপনাকে আপনার সম্পত্তি কর পরিস্থিতি বুঝতে সাহায্য করবে, কিন্তু আপিল বা বিরোধের জড়িত জটিল আইনি বিষয়ের জন্য, আমরা সম্পত্তি কর আইনজীবীর সাথে পরামর্শের সুপারিশ করতে পারি।"
    },

    PropertyTaxDomain.APPEAL: {
        "en": "I can guide you through the general appeal process, but specific legal strategies should be discussed with a qualified property tax consultant or attorney.",
        "hi": "मैं आपको सामान्य अपील प्रक्रिया के माध्यम से मार्गदर्शन कर सकता हूं, लेकिन विशिष्ट कानूनी रणनीतियों पर योग्य संपत्ति कर सलाहकार या वकील के साथ चर्चा करनी चाहिए।",
        "bn": "আমি আপনাকে সাধারণ আপিল প্রক্রিয়ার মাধ্যমে গাইড করতে পারি, কিন্তু নির্দিষ্ট আইনি কৌশল যোগ্য সম্পত্তি কর পরামর্শদাতা বা আইনজীবীর সাথে আলোচনা করা উচিত।"
    },

    PropertyTaxDomain.GENERAL_INQUIRY: {
        "en": "This information is provided for educational purposes only and does not constitute legal advice. For complex property tax matters, please consult with a licensed property tax consultant or attorney.",
        "hi": "यह जानकारी केवल शैक्षिक उद्देश्यों के लिए प्रदान की गई है और कानूनी सलाह नहीं है। जटिल संपत्ति कर मामलों के लिए, कृपया लाइसेंस प्राप्त संपत्ति कर सलाहकार या वकील से सलाह लें।",
        "bn": "এই তথ্য শুধুমাত্র শিক্ষামূলক উদ্দেশ্যে প্রদান করা হয়েছে এবং এটি আইনি পরামর্শ নয়। জটিল সম্পত্তি কর বিষয়ের জন্য, অনুগ্রহ করে লাইসেন্সপ্রাপ্ত সম্পত্তি কর পরামর্শদাতা বা আইনজীবীর সাথে পরামর্শ করুন।"
    }
}

class PropertyTaxAIConfig:
    """Central AI configuration manager for property tax domain"""

    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        if not self.google_api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables")

    def get_model_config(self, use_case: str) -> AIModelConfig:
        """Get AI model configuration for specific use case"""
        return AI_MODEL_CONFIGS.get(use_case, AI_MODEL_CONFIGS["text_conversation"])

    def get_domain_config(self, domain: PropertyTaxDomain) -> DomainConfig:
        """Get domain-specific configuration"""
        return DOMAIN_CONFIGS.get(domain, DOMAIN_CONFIGS[PropertyTaxDomain.GENERAL_INQUIRY])

    def should_escalate(self, domain: PropertyTaxDomain, user_message: str, confidence: float) -> bool:
        """Determine if conversation should be escalated to human agent"""
        domain_config = self.get_domain_config(domain)

        # Check confidence threshold
        if confidence < domain_config.confidence_threshold:
            return True

        # Check for escalation triggers
        message_lower = user_message.lower()
        for trigger in domain_config.recommended_escalation_triggers:
            if any(keyword in message_lower for keyword in trigger.split()):
                return True

        return False

    def get_legal_disclaimer(self, domain: PropertyTaxDomain, language: str = "en") -> str:
        """Get appropriate legal disclaimer for domain and language"""
        domain_disclaimers = LEGAL_DISCLAIMERS.get(domain, LEGAL_DISCLAIMERS[PropertyTaxDomain.GENERAL_INQUIRY])
        return domain_disclaimers.get(language, domain_disclaimers["en"])

    def validate_response_length(self, domain: PropertyTaxDomain, response: str) -> bool:
        """Validate if response length is appropriate for domain"""
        domain_config = self.get_domain_config(domain)
        return len(response) <= domain_config.max_response_length

    def get_texas_property_tax_info(self, info_type: str) -> Any:
        """Get Texas property tax specific information"""
        return TEXAS_PROPERTY_TAX_CONFIG.get(info_type, {})

    def is_within_legal_boundaries(self, domain: PropertyTaxDomain, user_request: str) -> Tuple[bool, List[str]]:
        """Check if user request is within legal boundaries"""
        domain_config = self.get_domain_config(domain)
        request_lower = user_request.lower()

        violations = []

        # Check against legal boundaries
        boundary_keywords = {
            "guarantee": ["guarantee", "promise", "ensure", "certain"],
            "legal_advice": ["legal advice", "should I", "what should I do legally"],
            "representation": ["represent me", "file for me", "speak for me"],
            "official_capacity": ["official", "certified", "authorize"]
        }

        for violation_type, keywords in boundary_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                violations.append(violation_type)

        return len(violations) == 0, violations

    def format_response_with_disclaimers(self, domain: PropertyTaxDomain, response: str, language: str = "en") -> str:
        """Format response with appropriate disclaimers"""
        domain_config = self.get_domain_config(domain)

        if domain_config.requires_disclaimer:
            disclaimer = self.get_legal_disclaimer(domain, language)
            return f"{response}\n\n{disclaimer}"

        return response

    def get_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """Convert confidence score to confidence level"""
        if confidence_score >= 0.9:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.7:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.5:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN

# Global AI configuration instance
_ai_config = None

def get_ai_config() -> PropertyTaxAIConfig:
    """Get or create the global AI configuration instance"""
    global _ai_config
    if _ai_config is None:
        _ai_config = PropertyTaxAIConfig()
        logger.info("🤖 Created property tax AI configuration")
    return _ai_config

# Utility functions for easy access
def get_model_for_use_case(use_case: str) -> str:
    """Get the appropriate model for a specific use case"""
    config = get_ai_config()
    model_config = config.get_model_config(use_case)
    return model_config.model_name

def should_escalate_conversation(domain: PropertyTaxDomain, message: str, confidence: float = 1.0) -> bool:
    """Check if conversation should be escalated"""
    config = get_ai_config()
    return config.should_escalate(domain, message, confidence)

def add_legal_disclaimer(domain: PropertyTaxDomain, response: str, language: str = "en") -> str:
    """Add appropriate legal disclaimer to response"""
    config = get_ai_config()
    return config.format_response_with_disclaimers(domain, response, language)

def validate_legal_boundaries(domain: PropertyTaxDomain, request: str) -> Tuple[bool, List[str]]:
    """Validate request against legal boundaries"""
    config = get_ai_config()
    return config.is_within_legal_boundaries(domain, request)

# Export key classes and functions
__all__ = [
    'AIModel',
    'PropertyTaxDomain',
    'ConfidenceLevel',
    'PropertyTaxAIConfig',
    'get_ai_config',
    'get_model_for_use_case',
    'should_escalate_conversation',
    'add_legal_disclaimer',
    'validate_legal_boundaries',
    'TEXAS_PROPERTY_TAX_CONFIG'
]