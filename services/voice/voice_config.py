"""
Century Property Tax Voice Configuration
Configuration settings for voice channel integration.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class VoiceConfig:
    """Voice agent configuration settings."""
    
    def __post_init__(self):
        """Initialize complex fields after creation."""
        # No hardcoded patterns - using LLM intelligence instead
    
    # LiveKit Configuration
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "wss://voice.centuryproptax.com")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "devkey")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "secret")
    
    # Google AI Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Voice Model Settings
    VOICE_MODEL: str = "gemini-live-2.5-flash-preview"
    VOICE_PERSONA: str = "Alex"  # Professional, clear voice
    VOICE_LANGUAGE: str = "en-IN"   # Indian English
    VOICE_TEMPERATURE: float = 0.2  # Conservative for property tax advice
    
    # Voice Detection Settings (Optimized for Indian English + Hindi)
    VAD_PREFIX_PADDING_MS: int = 500     # Account for Indian speech patterns
    VAD_SILENCE_DURATION_MS: int = 1200  # Longer pause for deliberate speech
    VAD_THRESHOLD: float = 0.5           # Accommodate diverse accents
    
    # Property Tax Settings - Using LLM-based assessment for complex tax queries
    
    # Supported Languages
    SUPPORTED_LANGUAGES: Dict[str, str] = {
        'english': 'en-IN',
        'hindi': 'hi-IN',
        'bengali': 'bn-IN',
        'tamil': 'ta-IN',
        'telugu': 'te-IN',
        'marathi': 'mr-IN',
        'gujarati': 'gu-IN',
        'kannada': 'kn-IN',
        'malayalam': 'ml-IN',
        'punjabi': 'pa-IN'
    }
    
    # Business Hours (24/7 for voice, but different services)
    BUSINESS_HOURS = {
        'consultations': {'start': 9, 'end': 17},      # 9 AM - 5 PM
        'document_services': {'start': 9, 'end': 18}, # 9 AM - 6 PM
        'voice_support': {'start': 0, 'end': 24},   # 24/7
        'urgent_assistance': {'start': 0, 'end': 24}  # 24/7
    }
    
    # Voice Response Templates
    GREETING_TEMPLATES: Dict[str, str] = {
        'english': """Hello, this is Alex from Century Property Tax. I'm here to help you with
                     property tax calculations, assessment appeals, payment assistance, or document services.
                     For your convenience, I can speak in Hindi or English - which language would you prefer?
                     And how may I assist you with your property tax needs today?""",

        'hindi': """Namaste, main Alex hun Century Property Tax se. Main aapki property tax calculation,
                   assessment appeal, payment assistance, ya document services mein madad kar sakti hun.
                   Aap Hindi ya English mein baat karna chahenge? Aur main aaj aapki property tax needs
                   mein kaise madad kar sakti hun?""",
    }
    
    URGENT_ESCALATION_MESSAGE: str = """⚠️ This sounds like an urgent property tax matter requiring
    immediate attention. Please contact your local tax authority or visit their office during
    business hours. Century Property Tax provides consultation and assistance, but for legal deadlines
    and official matters, please contact the appropriate government office directly."""
    
    # Payment Configuration
    PAYMENT_METHODS: List[str] = ['online', 'cash', 'card']
    PAYMENT_TIMEOUT_HOURS: int = 24
    
    # Integration Settings
    WEBHOOK_TIMEOUT_SECONDS: int = 30
    DATABASE_TIMEOUT_SECONDS: int = 10
    REDIS_TIMEOUT_SECONDS: int = 5
    
    # Quality Settings
    AUDIO_QUALITY: str = "high"
    ECHO_CANCELLATION: bool = True
    NOISE_SUPPRESSION: bool = True
    
    # Compliance Settings
    RECORD_CALLS: bool = True  # For quality and compliance
    DATA_RETENTION_DAYS: int = 90  # DPDP Act 2023 compliance
    CONSENT_REQUIRED: bool = True
    
    # Error Handling
    MAX_RETRY_ATTEMPTS: int = 3
    FALLBACK_TO_HUMAN: bool = True
    ESCALATION_THRESHOLD_SECONDS: int = 300  # 5 minutes

    def get_turn_detection_config(self) -> Dict:
        """Get voice activity detection configuration."""
        return {
            "type": "server_vad",
            "prefix_padding_ms": self.VAD_PREFIX_PADDING_MS,
            "silence_duration_ms": self.VAD_SILENCE_DURATION_MS,
            "threshold": self.VAD_THRESHOLD
        }
    
    async def assess_urgency_with_llm(self, query: str) -> Dict[str, Any]:
        """Use LLM to intelligently assess if property tax query requires urgent attention."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage, SystemMessage
            
            model = ChatGoogleGenerativeAI(
                model=self.VOICE_MODEL,
                temperature=self.VOICE_TEMPERATURE
            )

            prompt = f"""
Assess if this property tax query requires urgent attention with deadlines or legal implications: {query}

Respond with:
URGENT: [reason] OR NON_URGENT: [reason]
"""
            
            response = model.invoke([SystemMessage(content=prompt)])
            
            is_urgent = response.content.strip().startswith("URGENT:")
            explanation = response.content.replace("URGENT:" if is_urgent else "NON_URGENT:", "").strip()

            return {
                'is_urgent': is_urgent,
                'explanation': explanation,
                'confidence': 'high' if 'deadline' in query.lower() else 'medium'
            }
            
        except Exception as e:
            # Conservative fallback - always err on the side of caution for legal deadlines
            return {
                'is_urgent': True,
                'explanation': 'Unable to assess - please contact tax authority for time-sensitive matters',
                'confidence': 'fallback'
            }
    
    def get_language_code(self, language: str) -> str:
        """Get language code for voice synthesis."""
        return self.SUPPORTED_LANGUAGES.get(language.lower(), 'en-IN')
    
    def is_business_hours(self, service_type: str = 'voice_support') -> bool:
        """Check if current time is within business hours for service."""
        from datetime import datetime
        current_hour = datetime.now().hour
        hours = self.BUSINESS_HOURS.get(service_type, {'start': 0, 'end': 24})
        return hours['start'] <= current_hour < hours['end']

# Global configuration instance
voice_config = VoiceConfig()