"""
AUREN AI Gateway - Intelligent LLM routing and management.

Provides a unified interface for accessing multiple LLM providers
with intelligent routing, cost tracking, and fault tolerance.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

from .providers import BaseLLMProvider, OpenAIProvider, SelfHostedProvider, LLMResponse
from .models import ModelSelector
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .adaptive_circuit_breaker import AdaptiveCircuitBreaker
from .resilient_token_tracker import ResilientTokenTracker
from .adaptive_health_checker import AdaptiveHealthChecker, AdaptiveHealthManager
from .pricing_calculator import SelfHostedPricingCalculator

logger = logging.getLogger(__name__)


@dataclass
class GatewayRequest:
    """Request to the AI Gateway."""
    prompt: str
    user_id: str
    model_preference: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    budget_limit: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GatewayResponse:
    """Response from the AI Gateway."""
    content: str
    model_used: str
    provider_used: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    response_time: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AIGateway:
    """Main AI Gateway for intelligent LLM routing."""
    
    def __init__(self):
        self.model_selector = ModelSelector()
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.circuit_breakers: Dict[str, AdaptiveCircuitBreaker] = {}
        self.token_tracker = ResilientTokenTracker()
        self.health_manager = AdaptiveHealthManager()
        self.pricing_calculator = SelfHostedPricingCalculator()
        
        self._initialize_providers()
        self._initialize_circuit_breakers()
        
    def _initialize_providers(self):
        """Initialize available providers."""
        # OpenAI Provider (with environment variables)
        openai_api_key = os.getenv("OPENAI_API_KEY", "dummy_key")
        self.providers["openai"] = OpenAIProvider(
            model_name="gpt-3.5-turbo",
            api_key=openai_api_key
        )
        
        # Self-hosted providers
        self.providers["self_hosted"] = SelfHostedProvider(
            endpoint_url="http://localhost:8000",
            model_name="llama-3.1-70b"
        )
        
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for each provider."""
        for provider_name in self.providers:
            config = CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30,
                success_threshold=1,
                recovery_timeout_overrides={
                    "rate_limit": 5.0,
                    "timeout": 15.0
                }
            )
            
            self.circuit_breakers[provider_name] = AdaptiveCircuitBreaker(
                config, provider_name
            )
            
    async def complete(self, request: GatewayRequest) -> GatewayResponse:
        """
        Complete a prompt using the optimal provider.
        
        Args:
            request: The gateway request
            
        Returns:
            GatewayResponse with the completion
        """
        start_time = datetime.now()
        
        # Check user budget
        user_stats = await self.token_tracker.get_user_stats(request.user_id)
        remaining_budget = user_stats.get("today", {}).get("remaining", float("inf"))
        
        if request.budget_limit and request.budget_limit < remaining_budget:
            remaining_budget = request.budget_limit
            
        # Check if budget is too low for any request
        if remaining_budget < 0.02:  # Minimum budget threshold
            raise ValueError(f"Insufficient budget: ${remaining_budget:.4f} remaining. Minimum required: $0.02")
            
        # Select optimal model
        # If user has a preference for speed, set prefer_fast
        prefer_fast = request.model_preference == "fast" if request.model_preference else False
        
        selected_model = self.model_selector.select_model(
            prompt=request.prompt,
            remaining_budget=remaining_budget,
            available_models=list(self.providers.keys()),
            prefer_fast=prefer_fast
        )
        
        if not selected_model:
            raise ValueError("No suitable model found for request")
            
        provider = self.providers[selected_model]
        circuit_breaker = self.circuit_breakers[selected_model]
        
        # Make the call through circuit breaker
        try:
            llm_response = await circuit_breaker.call(
                provider.complete,
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            # Track usage
            await self.token_tracker.track_usage(
                user_id=request.user_id,
                model=selected_model,
                prompt_tokens=llm_response.prompt_tokens,
                completion_tokens=llm_response.completion_tokens,
                cost=llm_response.cost
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return GatewayResponse(
                content=llm_response.content,
                model_used=llm_response.model,
                provider_used=selected_model,
                prompt_tokens=llm_response.prompt_tokens,
                completion_tokens=llm_response.completion_tokens,
                total_tokens=llm_response.total_tokens,
                cost=llm_response.cost,
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"Error in gateway completion: {e}")
            raise
            
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get usage statistics for a user."""
        return await self.token_tracker.get_user_stats(user_id)
        
    async def set_user_budget(self, user_id: str, daily_budget: float):
        """Set daily budget for a user."""
        await self.token_tracker.set_user_budget(user_id, daily_budget)
        
    def get_provider_health(self) -> Dict[str, Any]:
        """Get health status of all providers."""
        return self.health_manager.get_health_summary()
        
    def get_cost_comparison(self, model: str) -> Dict[str, Any]:
        """Get cost comparison for a model."""
        return self.pricing_calculator.compare_with_commercial(model)


class CrewAIGateway:
    """CrewAI-compatible gateway interface."""
    
    def __init__(self, gateway: Optional[AIGateway] = None):
        self.gateway = gateway or AIGateway()
        
    async def complete(
        self,
        prompt: str,
        user_id: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """CrewAI-compatible completion method."""
        request = GatewayRequest(
            prompt=prompt,
            user_id=user_id,
            model_preference=model,
            **kwargs
        )
        
        response = await self.gateway.complete(request)
        return response.content
        
    async def get_cost_estimate(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 1000
    ) -> float:
        """Get cost estimate for a prompt."""
        model_config = self.gateway.model_selector.models.get(model)
        if not model_config:
            return 0.0
            
        return model_config.estimate_cost(
            prompt_tokens=len(prompt.split()),
            completion_tokens=max_tokens
        )


# Global gateway instance (lazy initialization)
_ai_gateway_instance: Optional[AIGateway] = None


def get_ai_gateway() -> AIGateway:
    """Get the global AI gateway instance."""
    global _ai_gateway_instance
    if _ai_gateway_instance is None:
        _ai_gateway_instance = AIGateway()
    return _ai_gateway_instance
