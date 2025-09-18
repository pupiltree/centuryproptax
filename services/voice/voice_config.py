"""
Krishna Diagnostics Voice Configuration
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
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "wss://livekit.krishnadiagnostics.ai")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "devkey")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "secret")
    
    # Google AI Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Voice Model Settings
    VOICE_MODEL: str = "gemini-live-2.5-flash-preview"
    VOICE_PERSONA: str = "Charon"  # Professional, clear voice
    VOICE_LANGUAGE: str = "en-IN"   # Indian English
    VOICE_TEMPERATURE: float = 0.2  # Conservative for healthcare
    
    # Voice Detection Settings (Optimized for Indian English + Hindi)
    VAD_PREFIX_PADDING_MS: int = 500     # Account for Indian speech patterns
    VAD_SILENCE_DURATION_MS: int = 1200  # Longer pause for deliberate speech
    VAD_THRESHOLD: float = 0.5           # Accommodate diverse accents
    
    # Healthcare Settings - Using LLM-based emergency assessment instead of keywords
    
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
        'lab_visits': {'start': 6, 'end': 22},      # 6 AM - 10 PM
        'home_collection': {'start': 7, 'end': 21}, # 7 AM - 9 PM
        'voice_support': {'start': 0, 'end': 24},   # 24/7
        'emergency_escalation': {'start': 0, 'end': 24}  # 24/7
    }
    
    # Voice Response Templates
    GREETING_TEMPLATES: Dict[str, str] = {
        'english': """Hello, this is Maya from Krishna Diagnostics. I'm here to help you with 
                     diagnostic test booking, test information, or report status. For your convenience, 
                     I can speak in Hindi or English - which language would you prefer? 
                     And how may I assist you with your healthcare needs today?""",
        
        'hindi': """Namaste, main Maya hun Krishna Diagnostics se. Main aapki diagnostic test booking, 
                   test ki jaankari, ya report status mein madad kar sakti hun. Aap Hindi ya English 
                   mein baat karna chahenge? Aur main aaj aapki healthcare needs mein kaise madad kar sakti hun?""",
    }
    
    EMERGENCY_ESCALATION_MESSAGE: str = """⚠️ This sounds like a medical emergency. Please call 108 
    (India Emergency) or go to the nearest hospital immediately. Krishna Diagnostics provides 
    diagnostic testing, not emergency medical care. Please seek immediate medical attention 
    from a qualified doctor."""
    
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
    
    async def assess_emergency_with_llm(self, symptoms: str) -> Dict[str, Any]:
        """Use LLM to intelligently assess if symptoms indicate a medical emergency."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage, SystemMessage
            
            model = ChatGoogleGenerativeAI(
                model=self.EMERGENCY_ASSESSMENT_MODEL, 
                temperature=self.EMERGENCY_ASSESSMENT_TEMPERATURE
            )
            
            prompt = f"""
Assess if these symptoms indicate a medical emergency requiring immediate hospital care: {symptoms}

Respond with:
EMERGENCY: [reason] OR NON_EMERGENCY: [reason]
"""
            
            response = model.invoke([SystemMessage(content=prompt)])
            
            is_emergency = response.content.strip().startswith("EMERGENCY:")
            explanation = response.content.replace("EMERGENCY:" if is_emergency else "NON_EMERGENCY:", "").strip()
            
            return {
                'is_emergency': is_emergency,
                'explanation': explanation,
                'confidence': 'high' if 'severe' in symptoms.lower() else 'medium'
            }
            
        except Exception as e:
            # Conservative fallback - always err on the side of medical safety
            return {
                'is_emergency': True,
                'explanation': 'Unable to assess - please seek medical attention for safety',
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