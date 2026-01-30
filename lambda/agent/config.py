"""
Configuration settings for Jarvis
For Alexa-hosted skills, set these as environment variables in AWS Lambda
"""
import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        # OpenAI - REQUIRED
        self.openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
        self.openai_model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")
        self.openai_model_cheap: str = os.environ.get("OPENAI_MODEL_CHEAP", "gpt-4o-mini")
        
        # Supabase - REQUIRED
        self.supabase_url: str = os.environ.get("SUPABASE_URL", "")
        self.supabase_key: str = os.environ.get("SUPABASE_KEY", "")
        
        # Weather API - OPTIONAL
        self.openweather_api_key: Optional[str] = os.environ.get("OPENWEATHER_API_KEY")
        
        # Twilio for WhatsApp - OPTIONAL
        self.twilio_account_sid: Optional[str] = os.environ.get("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token: Optional[str] = os.environ.get("TWILIO_AUTH_TOKEN")
        self.twilio_whatsapp_from: Optional[str] = os.environ.get("TWILIO_WHATSAPP_FROM")
        self.approval_whatsapp_to: Optional[str] = os.environ.get("APPROVAL_WHATSAPP_TO")
        
        # Agent settings
        self.max_conversation_messages: int = int(os.environ.get("MAX_CONVERSATION_MESSAGES", "20"))
        self.max_response_length: int = int(os.environ.get("MAX_RESPONSE_LENGTH", "300"))
        self.default_user_id: str = os.environ.get("DEFAULT_USER_ID", "default-family-user")
    
    def validate(self) -> bool:
        """Check if required settings are present"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not self.supabase_key:
            raise ValueError("SUPABASE_KEY environment variable is required")
        return True


# Global settings instance
settings = Settings()
