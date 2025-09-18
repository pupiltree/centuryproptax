"""Application settings for Krsnaa Diagnostics AI Chatbot."""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()


class Settings:
    """Application settings with environment variable support."""
    
    # Instagram Configuration
    ig_token: str = os.getenv("IG_TOKEN", "")
    ig_user_id: str = os.getenv("IG_USER_ID", "")  
    verify_token: str = os.getenv("VERIFY_TOKEN", "")
    
    # Meta App Configuration (not currently used in production)
    
    # Gemini AI Configuration
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemini_model_pro: str = os.getenv("GEMINI_MODEL_PRO", "gemini-2.5-pro")
    gemini_model_flash: str = os.getenv("GEMINI_MODEL_FLASH", "gemini-2.5-flash")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///krishna_diagnostics.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # State Persistence Configuration
    state_key_prefix: str = os.getenv("STATE_KEY_PREFIX", "conversation_state")
    state_persistence_ttl: int = int(os.getenv("STATE_PERSISTENCE_TTL", "86400"))  # 24 hours
    
    # Agent Configuration (legacy options - not currently used)
    
    # Application Configuration
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "test_secret_key_for_development_only")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate essential configuration."""
        required_vars = [
            ("IG_TOKEN", cls.ig_token),
            ("IG_USER_ID", cls.ig_user_id),
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
        print(f"   IG_TOKEN: {'✅ Set' if cls.ig_token else '❌ Missing'}")
        print(f"   IG_USER_ID: {cls.ig_user_id}")
        print(f"   VERIFY_TOKEN: {'✅ Set' if cls.verify_token else '❌ Missing'}")
        print(f"   GOOGLE_API_KEY: {'✅ Set' if cls.google_api_key else '❌ Missing'}")
        print(f"   DEBUG: {cls.debug}")
        print(f"   LOG_LEVEL: {cls.log_level}")


# Global settings instance
settings = Settings()

# Validate on import
if __name__ == "__main__":
    settings.print_config()
    settings.validate()