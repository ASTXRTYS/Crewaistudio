"""
AUREN AI Gateway - Intelligent LLM routing and management.

Provides a unified interface for accessing multiple LLM providers
with intelligent routing, cost tracking, and fault tolerance.
"""

from typing import Optional

from .gateway import AIGateway, CrewAIGateway, GatewayRequest, GatewayResponse
from .providers import (
    BaseLLMProvider,
    OpenAIProvider,
    SelfHostedProvider,
    LLMResponse
)
from .models import ModelSelector
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .adaptive_circuit_breaker import AdaptiveCircuitBreaker
from .resilient_token_tracker import ResilientTokenTracker
from .adaptive_health_checker import AdaptiveHealthChecker, AdaptiveHealthManager
from .pricing_calculator import SelfHostedPricingCalculator

# Export main components
__all__ = [
    "AIGateway",
    "CrewAIGateway",
    "GatewayRequest",
    "GatewayResponse",
    "BaseLLMProvider",
    "OpenAIProvider",
    "SelfHostedProvider",
    "LLMResponse",
    "ModelSelector",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "AdaptiveCircuitBreaker",
    "ResilientTokenTracker",
    "AdaptiveHealthChecker",
    "AdaptiveHealthManager",
    "SelfHostedPricingCalculator"
]

# Global gateway instance (lazy initialization)
_ai_gateway_instance: Optional[AIGateway] = None


def get_ai_gateway() -> AIGateway:
    """Get the global AI gateway instance."""
    global _ai_gateway_instance
    if _ai_gateway_instance is None:
        _ai_gateway_instance = AIGateway()
    return _ai_gateway_instance
