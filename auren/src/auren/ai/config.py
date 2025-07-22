"""
Configuration management for the AUREN AI Gateway.

This module handles environment-specific configuration loading with
Pydantic validation, including API keys, endpoints, and model pricing.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, validator, Field

logger = logging.getLogger(__name__)


class AIGatewayConfig(BaseModel):
    """Validated configuration with defaults and type checking."""
    
    model_config = {"protected_namespaces": ()}
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None)
    
    # Self-hosted endpoints
    llama_endpoint: str = Field(default="http://localhost:8000")
    meditron_endpoint: Optional[str] = Field(default=None)
    
    # Redis configuration
    redis_url: str = Field(default="redis://localhost:6379")
    
    # Budget configuration
    daily_budget_limit: float = Field(default=10.0, ge=0.0)
    
    # Token tracking configuration
    token_tracking_enabled: bool = Field(default=True)
    
    # Circuit breaker defaults
    circuit_breaker_failure_threshold: int = Field(default=5, ge=1)
    circuit_breaker_recovery_timeout: int = Field(default=60, ge=1)
    circuit_breaker_success_threshold: int = Field(default=2, ge=1)
    
    # Model pricing configuration (JSON string in env)
    model_pricing_config: Optional[Dict[str, Any]] = None
    
    # Circuit breaker configuration (JSON string in env)
    circuit_breaker_config: Optional[Dict[str, Any]] = None
    
    @validator('openai_api_key')
    def validate_api_key(cls, v):
        """Validate OpenAI API key format."""
        if v and not v.startswith('sk-'):
            logger.warning("OpenAI API key does not start with 'sk-', it may be invalid")
        return v
    
    @validator('llama_endpoint', 'meditron_endpoint')
    def validate_endpoint(cls, v):
        """Validate endpoint URLs."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError(f"Endpoint must start with http:// or https://: {v}")
        return v
    
    @validator('redis_url')
    def validate_redis_url(cls, v):
        """Validate Redis URL format."""
        if not v.startswith('redis://'):
            raise ValueError(f"Redis URL must start with redis://: {v}")
        return v
    
    @validator('model_pricing_config', pre=True)
    def parse_model_pricing(cls, v):
        """Parse model pricing from JSON string."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid MODEL_PRICING_CONFIG JSON: {e}")
                return None
        return v
    
    @validator('circuit_breaker_config', pre=True)
    def parse_circuit_breaker_config(cls, v):
        """Parse circuit breaker config from JSON string."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid CIRCUIT_BREAKER_CONFIG JSON: {e}")
                return None
        return v
    
    def is_configured(self) -> bool:
        """Check if at least one provider is configured."""
        return bool(self.openai_api_key or self.llama_endpoint or self.meditron_endpoint)
    
    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        configs = {
            "openai": {
                "api_key": self.openai_api_key,
                "enabled": bool(self.openai_api_key)
            },
            "llama": {
                "endpoint": self.llama_endpoint,
                "enabled": bool(self.llama_endpoint)
            },
            "meditron": {
                "endpoint": self.meditron_endpoint,
                "enabled": bool(self.meditron_endpoint)
            }
        }
        return configs.get(provider_name, {})
    
    def get_circuit_breaker_config(self, provider_name: str) -> Dict[str, Any]:
        """Get circuit breaker configuration for a provider."""
        if self.circuit_breaker_config and provider_name in self.circuit_breaker_config:
            return self.circuit_breaker_config[provider_name]
        
        # Return defaults based on provider type
        if provider_name == "openai":
            return {
                "failure_threshold": self.circuit_breaker_failure_threshold,
                "recovery_timeout": self.circuit_breaker_recovery_timeout,
                "success_threshold": self.circuit_breaker_success_threshold
            }
        else:
            # Self-hosted services may need longer recovery times
            return {
                "failure_threshold": 3,
                "recovery_timeout": 120,
                "success_threshold": 1
            }
    
    def get_model_pricing(self) -> Dict[str, Any]:
        """Get model pricing configuration."""
        if self.model_pricing_config:
            return self.model_pricing_config
        return DEFAULT_MODEL_PRICING
    



# For backward compatibility
AIConfig = AIGatewayConfig


def load_config() -> AIGatewayConfig:
    """Load and validate configuration from environment variables."""
    try:
        # Load from environment variables
        config_data = {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "llama_endpoint": os.getenv("LLAMA_ENDPOINT", "http://localhost:8000"),
            "meditron_endpoint": os.getenv("MEDITRON_ENDPOINT"),
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "daily_budget_limit": float(os.getenv("DAILY_BUDGET_LIMIT", "10.0")),
            "token_tracking_enabled": os.getenv("TOKEN_TRACKING_ENABLED", "true").lower() == "true",
            "circuit_breaker_failure_threshold": int(os.getenv("CB_FAILURE_THRESHOLD", "5")),
            "circuit_breaker_recovery_timeout": int(os.getenv("CB_RECOVERY_TIMEOUT", "60")),
            "circuit_breaker_success_threshold": int(os.getenv("CB_SUCCESS_THRESHOLD", "2")),
            "model_pricing_config": os.getenv("MODEL_PRICING_CONFIG"),
            "circuit_breaker_config": os.getenv("CIRCUIT_BREAKER_CONFIG")
        }
        
        config = AIGatewayConfig(**config_data)
        logger.info("Configuration loaded successfully")
        
        if not config.is_configured():
            logger.warning("No AI providers configured. Please set OPENAI_API_KEY or self-hosted endpoints.")
        
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


# Environment-specific configuration files
ENV_CONFIG_FILES = {
    "development": ".env.development",
    "staging": ".env.staging",
    "production": ".env.production"
}


def load_env_file(env: str = None) -> None:
    """
    Load environment-specific configuration file.
    
    Args:
        env: Environment name (development, staging, production)
             If None, uses ENVIRONMENT variable or defaults to development
    """
    if env is None:
        env = os.getenv("ENVIRONMENT", "development")
        
    config_file = ENV_CONFIG_FILES.get(env, ".env.development")
    
    if Path(config_file).exists():
        from dotenv import load_dotenv
        load_dotenv(config_file)
        logger.info(f"Loaded configuration from {config_file}")
    else:
        logger.warning(f"Configuration file {config_file} not found, using environment variables")


# Default model pricing configuration
DEFAULT_MODEL_PRICING = {
    "gpt-3.5-turbo": {
        "provider": "openai",
        "input_cost_per_1k": 1.50,
        "output_cost_per_1k": 2.00,
        "max_tokens": 4096,
        "quality_tier": "medium",
        "speed_tier": "fast"
    },
    "gpt-4-turbo": {
        "provider": "openai",
        "input_cost_per_1k": 10.00,
        "output_cost_per_1k": 30.00,
        "max_tokens": 4096,
        "quality_tier": "high",
        "speed_tier": "medium"
    },
    "gpt-4": {
        "provider": "openai",
        "input_cost_per_1k": 30.00,
        "output_cost_per_1k": 60.00,
        "max_tokens": 8192,
        "quality_tier": "premium",
        "speed_tier": "slow"
    },
    "llama-3.1-70b": {
        "provider": "self_hosted",
        "input_cost_per_1k": 0.50,
        "output_cost_per_1k": 0.50,
        "max_tokens": 4096,
        "quality_tier": "high",
        "speed_tier": "medium"
    },
    "meditron-70b": {
        "provider": "self_hosted",
        "input_cost_per_1k": 0.50,
        "output_cost_per_1k": 0.50,
        "max_tokens": 4096,
        "quality_tier": "high",
        "speed_tier": "medium"
    }
}


# Validation on module import
if __name__ == "__main__":
    # Test configuration loading
    config = load_config()
    print(f"Configuration loaded: {config.dict()}")
