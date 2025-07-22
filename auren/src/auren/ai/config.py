"""
Configuration management for the AUREN AI Gateway.

This module handles environment-specific configuration loading,
including API keys, endpoints, and model pricing.
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AIConfig:
    """Centralized configuration for the AI Gateway."""
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    
    # Self-hosted endpoints
    llama_endpoint: Optional[str] = None
    meditron_endpoint: Optional[str] = None
    
    # Model pricing configuration
    model_pricing_config: Dict[str, Any] = None
    
    # Circuit breaker configuration
    circuit_breaker_config: Dict[str, Any] = None
    
    # Budget configuration
    daily_budget_limit: float = 10.0  # Default $10/day
    
    # Token tracking configuration
    token_tracking_enabled: bool = True
    
    def __post_init__(self):
        """Load configuration from environment variables."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.llama_endpoint = os.getenv("LLAMA_ENDPOINT")
        self.meditron_endpoint = os.getenv("MEDITRON_ENDPOINT")
        self.daily_budget_limit = float(os.getenv("DAILY_BUDGET_LIMIT", "10.0"))
        self.token_tracking_enabled = os.getenv("TOKEN_TRACKING_ENABLED", "true").lower() == "true"
        
        # Load model pricing from environment
        pricing_json = os.getenv("MODEL_PRICING_CONFIG")
        if pricing_json:
            try:
                self.model_pricing_config = json.loads(pricing_json)
            except json.JSONDecodeError:
                self.model_pricing_config = None
                
        # Load circuit breaker config from environment
        breaker_json = os.getenv("CIRCUIT_BREAKER_CONFIG")
        if breaker_json:
            try:
                self.circuit_breaker_config = json.loads(breaker_json)
            except json.JSONDecodeError:
                self.circuit_breaker_config = None
                
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


def load_config() -> AIConfig:
    """Load configuration from environment variables."""
    return AIConfig()


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


# Default circuit breaker configuration
DEFAULT_CIRCUIT_BREAKER_CONFIG = {
    "openai": {
        "failure_threshold": 5,
        "recovery_timeout": 30,
        "success_threshold": 2
    },
    "self_hosted": {
        "failure_threshold": 3,
        "recovery_timeout": 120,
        "success_threshold": 1
    }
}


# Initialize logger
import logging
logger = logging.getLogger(__name__)
