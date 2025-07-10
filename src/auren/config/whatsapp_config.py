import os
from typing import Optional

class WhatsAppConfig:
    """WhatsApp configuration with dev/prod modes"""
    
    def __init__(self, mode: str = None):
        self.mode = mode or os.getenv("AUREN_ENV", "development")
        
        if self.mode == "development":
            # Use mock values for development
            self.token = os.getenv("WHATSAPP_TOKEN", "mock_token_dev")
            self.app_secret = os.getenv("WHATSAPP_APP_SECRET", "mock_secret_dev")
            self.phone_id = os.getenv("WHATSAPP_PHONE_ID", "mock_phone_dev")
            self.use_mock_api = True
        else:
            # Require real values for production
            self.token = os.getenv("WHATSAPP_TOKEN")
            self.app_secret = os.getenv("WHATSAPP_APP_SECRET")
            self.phone_id = os.getenv("WHATSAPP_PHONE_ID")
            self.use_mock_api = False
            
            if not all([self.token, self.app_secret, self.phone_id]):
                raise ValueError(
                    "Production mode requires all WhatsApp environment variables"
                )
    
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode"""
        return self.use_mock_api
    
    def get_webhook_url(self) -> str:
        """Get webhook URL for current mode"""
        if self.is_mock_mode():
            return "http://localhost:8504/webhook"
        else:
            # Production webhook URL
            return os.getenv("WHATSAPP_WEBHOOK_URL", "")
    
    def validate_config(self) -> bool:
        """Validate configuration for current mode"""
        if self.is_mock_mode():
            return True  # Mock mode always valid
        else:
            return all([self.token, self.app_secret, self.phone_id]) 