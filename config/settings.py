"""Application settings for Century Property Tax AI Chatbot."""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()


class Settings:
    """Application settings with environment variable support."""
    
    # WhatsApp Configuration
    whatsapp_token: str = os.getenv("WHATSAPP_TOKEN", "")
    whatsapp_phone_id: str = os.getenv("WHATSAPP_PHONE_ID", "")
    verify_token: str = os.getenv("VERIFY_TOKEN", "")
    
    # Gemini AI Configuration
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemini_model_pro: str = os.getenv("GEMINI_MODEL_PRO", "gemini-2.5-pro")
    gemini_model_flash: str = os.getenv("GEMINI_MODEL_FLASH", "gemini-2.5-flash")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///century_property_tax.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # State Persistence Configuration
    state_key_prefix: str = os.getenv("STATE_KEY_PREFIX", "property_tax_conversation")
    state_persistence_ttl: int = int(os.getenv("STATE_PERSISTENCE_TTL", "86400"))  # 24 hours

    # Application Configuration
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "test_secret_key_for_development_only")

    # Property Tax Specific Configuration
    property_tax_calculator_api_url: str = os.getenv("PROPERTY_TAX_CALCULATOR_API_URL", "https://api.centuryproptax.com/calculator")
    property_records_api_url: str = os.getenv("PROPERTY_RECORDS_API_URL", "https://api.centuryproptax.com/records")
    assessment_notification_api_url: str = os.getenv("ASSESSMENT_NOTIFICATION_API_URL", "https://api.centuryproptax.com/notifications")
    payment_portal_url: str = os.getenv("PAYMENT_PORTAL_URL", "https://payments.centuryproptax.com")

    # Encryption Keys
    property_data_encryption_key: Optional[str] = os.getenv("PROPERTY_DATA_ENCRYPTION_KEY")
    consultation_encryption_key: Optional[str] = os.getenv("CONSULTATION_ENCRYPTION_KEY")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate essential configuration."""
        required_vars = [
            ("WHATSAPP_TOKEN", cls.whatsapp_token),
            ("WHATSAPP_PHONE_ID", cls.whatsapp_phone_id),
            ("VERIFY_TOKEN", cls.verify_token),
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        print("✅ All required environment variables are configured")
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (safely)."""
        print("📋 Current Configuration:")
        print(f"   WHATSAPP_TOKEN: {'✅ Set' if cls.whatsapp_token else '❌ Missing'}")
        print(f"   WHATSAPP_PHONE_ID: {cls.whatsapp_phone_id}")
        print(f"   VERIFY_TOKEN: {'✅ Set' if cls.verify_token else '❌ Missing'}")
        print(f"   GOOGLE_API_KEY: {'✅ Set' if cls.google_api_key else '❌ Missing'}")
        print(f"   DEBUG: {cls.debug}")
        print(f"   LOG_LEVEL: {cls.log_level}")
        print(f"   PROPERTY_TAX_CALCULATOR_API: {'✅ Set' if cls.property_tax_calculator_api_url else '❌ Default'}")
        print(f"   PROPERTY_RECORDS_API: {'✅ Set' if cls.property_records_api_url else '❌ Default'}")
        print(f"   PAYMENT_PORTAL_URL: {'✅ Set' if cls.payment_portal_url else '❌ Default'}")


# Global settings instance
settings = Settings()

# Validate on import
if __name__ == "__main__":
    settings.print_config()
    settings.validate()