"""Configuration settings for the AUREN system.

This module centralizes all environment variables and configuration
settings with proper validation and defaults.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    user: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="auren_dev", env="DB_PASSWORD")
    name: str = Field(default="auren_development", env="DB_NAME")
    
    @property
    def url(self) -> str:
        """Get database URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    class Config:
        env_prefix = "DB_"


class AIProviderSettings(BaseSettings):
    """AI Provider configuration settings"""
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    
    class Config:
        env_prefix = ""


class WhatsAppSettings(BaseSettings):
    """WhatsApp configuration settings"""
    access_token: Optional[str] = Field(default=None, env="WHATSAPP_ACCESS_TOKEN")
    phone_id: Optional[str] = Field(default=None, env="WHATSAPP_PHONE_ID")
    webhook_verify_token: Optional[str] = Field(default=None, env="WHATSAPP_WEBHOOK_VERIFY_TOKEN")
    
    class Config:
        env_prefix = "WHATSAPP_"


class KafkaSettings(BaseSettings):
    """Kafka configuration settings"""
    bootstrap_servers: str = Field(default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    security_protocol: str = Field(default="PLAINTEXT", env="KAFKA_SECURITY_PROTOCOL")
    
    class Config:
        env_prefix = "KAFKA_"


class RedisSettings(BaseSettings):
    """Redis configuration settings"""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    
    @property
    def url(self) -> str:
        """Get Redis URL"""
        return f"redis://{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_prefix = "REDIS_"


class ApplicationSettings(BaseSettings):
    """General application settings"""
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # CrewAI settings
    crewai_max_iterations: int = Field(default=3, env="CREWAI_MAX_ITERATIONS")
    crewai_memory_enabled: bool = Field(default=True, env="CREWAI_MEMORY_ENABLED")
    
    # Token tracking settings
    token_tracking_enabled: bool = Field(default=True, env="TOKEN_TRACKING_ENABLED")
    token_budget_daily: int = Field(default=100000, env="TOKEN_BUDGET_DAILY")
    token_alert_threshold: float = Field(default=0.8, env="TOKEN_ALERT_THRESHOLD")
    
    # Monitoring settings
    otel_enabled: bool = Field(default=False, env="OTEL_ENABLED")
    otel_endpoint: str = Field(default="http://localhost:4317", env="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_service_name: str = Field(default="auren-neuroscientist", env="OTEL_SERVICE_NAME")
    
    # Test settings
    test_mode: bool = Field(default=False, env="TEST_MODE")
    test_user_id: str = Field(default="test_user_001", env="TEST_USER_ID")
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        env_prefix = ""


class Settings(BaseSettings):
    """Main settings class that combines all settings"""
    database: DatabaseSettings = DatabaseSettings()
    ai_providers: AIProviderSettings = AIProviderSettings()
    whatsapp: WhatsAppSettings = WhatsAppSettings()
    kafka: KafkaSettings = KafkaSettings()
    redis: RedisSettings = RedisSettings()
    app: ApplicationSettings = ApplicationSettings()
    
    def validate_required_settings(self) -> Dict[str, list]:
        """Validate that required settings are present"""
        missing = {
            "ai_providers": [],
            "whatsapp": [],
            "database": []
        }
        
        # Check AI providers (at least one should be configured)
        if not any([
            self.ai_providers.openai_api_key,
            self.ai_providers.anthropic_api_key,
            self.ai_providers.groq_api_key
        ]):
            missing["ai_providers"].append("At least one AI provider API key required")
        
        # Check WhatsApp settings if not in test mode
        if not self.app.test_mode:
            if not self.whatsapp.access_token:
                missing["whatsapp"].append("WHATSAPP_ACCESS_TOKEN")
            if not self.whatsapp.phone_id:
                missing["whatsapp"].append("WHATSAPP_PHONE_ID")
        
        # Remove empty lists
        missing = {k: v for k, v in missing.items() if v}
        
        return missing
    
    class Config:
        env_prefix = ""


# Create a singleton instance
settings = Settings()


# Convenience function to get settings
def get_settings() -> Settings:
    """Get the settings instance"""
    return settings


# Example usage
if __name__ == "__main__":
    # Print current settings
    print("Database URL:", settings.database.url)
    print("Redis URL:", settings.redis.url)
    print("Environment:", settings.app.environment)
    print("Debug mode:", settings.app.debug)
    
    # Validate required settings
    missing = settings.validate_required_settings()
    if missing:
        print("\nMissing required settings:")
        for category, items in missing.items():
            print(f"  {category}: {', '.join(items)}") 