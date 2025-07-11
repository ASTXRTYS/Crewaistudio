"""
Centralized configuration management for AUREN 2.0
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field
from pathlib import Path


class Config(BaseSettings):
    """Centralized configuration for AUREN 2.0"""
    
    # Application settings
    app_name: str = "AUREN 2.0"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Database settings
    database_url: str = Field(default="sqlite:///./auren.db", env="DATABASE_URL")
    
    # AI/ML settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    crewai_model: str = Field(default="gpt-4", env="CREWAI_MODEL")
    
    # Monitoring settings
    enable_monitoring: bool = Field(default=True, env="ENABLE_MONITORING")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # File paths
    data_dir: Path = Field(default=Path("./data"), env="DATA_DIR")
    logs_dir: Path = Field(default=Path("./logs"), env="LOGS_DIR")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment"""
    global _config
    _config = Config()
    return _config
