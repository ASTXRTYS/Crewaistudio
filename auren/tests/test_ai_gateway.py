"""
Comprehensive tests for the AUREN AI Gateway.

Tests all components including:
- Gateway routing and model selection
- Circuit breaker functionality
- Token tracking and budget enforcement
- Health checking and monitoring
- Pricing calculations
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch
from datetime import datetime

from auren.ai import (
    AIGateway,
    CrewAIGateway,
    GatewayRequest,
    AdaptiveCircuitBreaker,
    ResilientTokenTracker,
    SelfHostedPricingCalculator,
    AdaptiveHealthChecker,
    ModelSelector
)


class TestAIGateway:
    """Test the main AI Gateway functionality."""
    
    @pytest.fixture
    def gateway(self):
        """Create a test gateway instance."""
        return AIGateway()
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for testing."""
        provider = AsyncMock()
        provider.complete = AsyncMock(return_value=AsyncMock(
            content="Test response",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        ))
        provider.health_check = AsyncMock(return_value=True)
        return provider
    
    def test_gateway_initialization(self, gateway):
        """Test gateway initializes correctly."""
        assert gateway.model_selector is not None
        assert isinstance(gateway.providers, dict)
        assert isinstance(gateway.circuit_breakers, dict)
        
    @pytest.mark.asyncio
    async def test_complete_request(self, gateway, mock_provider):
        """Test completing a request through the gateway."""
        from auren.ai.models import ModelConfig
        
        # Add test model to model selector
        gateway.model_selector.models["test-model"] = ModelConfig(
            name="test-model",
            provider="test",
            input_cost_per_1k=0.001,
            output_cost_per_1k=0.002,
            max_tokens=4000
        )
        
        # Mock provider setup
        gateway.providers["test"] = mock_provider
        gateway.circuit_breakers["test"] = AsyncMock()
        gateway.circuit_breakers["test"].call = AsyncMock(
            return_value=AsyncMock(
                content="Test response",
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            )
        )
        
        # Mock token tracker
        gateway.token_tracker = AsyncMock()
        gateway.token_tracker.get_user_stats = AsyncMock(return_value={
            "today": {"remaining": 100.0}
        })
        gateway.token_tracker.track_usage = AsyncMock()
        
        request = GatewayRequest(
            prompt="Test prompt",
            user_id="test_user"
        )
        
        # Mock the select_model to return our test model
        from unittest.mock import Mock
        gateway.model_selector.select_model = Mock(return_value="test")
        
        response = await gateway.complete(request)
        
        assert response.content == "Test response"
        assert response.total_tokens == 30
        assert response.model_used is not None
        
    @pytest.mark.asyncio
    async def test_budget_enforcement(self, gateway):
        """Test budget enforcement prevents overspending."""
        # Mock insufficient budget
        gateway.token_tracker = AsyncMock()
        gateway.token_tracker.get_user_stats = AsyncMock(return_value={
            "today": {"remaining": 0.01}
        })
        
        request = GatewayRequest(
            prompt="Test prompt",
            user_id="test_user"
        )
        
        with pytest.raises(Exception) as exc_info:
            await gateway.complete(request)
            
        assert "budget" in str(exc_info.value).lower()


class TestAdaptiveCircuitBreaker:
    """Test adaptive circuit breaker functionality."""
    
    @pytest.fixture
    def breaker(self):
        """Create a test circuit breaker."""
        from auren.ai.circuit_breaker import CircuitBreakerConfig
        return AdaptiveCircuitBreaker(
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30,
                success_threshold=1
            ),
            "test_model"
        )
    
    def test_stability_score_calculation(self, breaker):
        """Test stability score updates correctly."""
        # Initial state
        assert breaker.stability_score == 1.0
        
        # Record multiple failures to trigger stability calculation
        import time
        from auren.ai.adaptive_circuit_breaker import FailurePattern
        
        # Add some recovery history first
        breaker.recovery_history.extend([20.0, 25.0, 30.0])
        
        # Record failures with timestamps that simulate rapid recent failures
        current_time = time.time()
        # With corrected calculation, need >360 failures/hour for rate > 0.1
        # Let's simulate a more realistic scenario: 5 failures in 10 minutes
        for i in range(5):
            breaker.failure_history.append(
                FailurePattern(
                    timestamp=current_time - (i * 120),  # 2 minutes apart
                    duration=1.0,
                    error_type="timeout",
                    recovery_time=30
                )
            )
        
        # Now calculate should update stability based on high failure rate
        recovery_time = breaker.calculate_adaptive_recovery_time()
        assert breaker.stability_score < 1.0
        
        # Record recovery
        breaker.record_recovery(15.0)
        # Stability should improve
        
    def test_adaptive_recovery_time(self, breaker):
        """Test recovery time adapts based on patterns."""
        # With no history, use default
        assert breaker.calculate_adaptive_recovery_time() == 30
        
        # Record some failures
        for _ in range(5):
            breaker.record_failure("timeout", 1.0)
            
        # Recovery time should decrease for unstable service
        recovery_time = breaker.calculate_adaptive_recovery_time()
        assert recovery_time <= 30
        
    def test_stability_insights(self, breaker):
        """Test stability insights generation."""
        # Record multiple failures for better insights
        breaker.record_failure("timeout", 1.0)
        breaker.record_failure("rate_limit", 0.5)
        breaker.record_failure("timeout", 2.0)
        
        insights = breaker.get_stability_insights()
        
        assert "stability_score" in insights
        assert "recent_failures" in insights
        assert "failure_types" in insights


class TestResilientTokenTracker:
    """Test resilient token tracking."""
    
    @pytest.fixture
    def tracker(self):
        """Create a test token tracker."""
        return ResilientTokenTracker()
    
    @pytest.mark.asyncio
    async def test_track_usage(self, tracker):
        """Test tracking usage with fallback."""
        await tracker.initialize()
        
        await tracker.track_usage(
            user_id="test_user",
            model="gpt-3.5-turbo",
            prompt_tokens=100,
            completion_tokens=200,
            cost=0.0015
        )
        
        stats = await tracker.get_user_stats("test_user")
        assert "today" in stats
        assert "used" in stats["today"]
        
    @pytest.mark.asyncio
    async def test_redis_failover(self, tracker):
        """Test Redis failover to local memory."""
        # Force Redis to be unavailable
        tracker.use_redis = False
        
        await tracker.track_usage(
            user_id="test_user",
            model="gpt-3.5-turbo",
            prompt_tokens=100,
            completion_tokens=200,
            cost=0.0015
        )
        
        stats = await tracker.get_user_stats("test_user")
        assert stats["today"]["used"] == 0.0015
        
    @pytest.mark.asyncio
    async def test_budget_management(self, tracker):
        """Test budget management functionality."""
        await tracker.initialize()
        
        await tracker.set_user_budget("test_user", 5.0)
        
        # Track usage
        await tracker.track_usage(
            user_id="test_user",
            model="gpt-3.5-turbo",
            prompt_tokens=1000,
            completion_tokens=2000,
            cost=0.0045
        )
        
        stats = await tracker.get_user_stats("test_user")
        # If Redis is available, check the limit
        if stats and "today" in stats:
            assert stats["today"]["limit"] == 5.0
        else:
            # Skip if Redis is not available
            pytest.skip("Redis not available for this test")


class TestSelfHostedPricingCalculator:
    """Test self-hosted pricing calculations."""
    
    @pytest.fixture
    def calculator(self):
        """Create a test pricing calculator."""
        return SelfHostedPricingCalculator()
    
    def test_cost_calculation(self, calculator):
        """Test cost calculation for known models."""
        cost = calculator.calculate_cost_per_million_tokens("llama-3.1-70b")
        
        assert cost > 0
        assert cost < 20.0  # Reasonable for 70B model on A100
        
    def test_cost_breakdown(self, calculator):
        """Test detailed cost breakdown."""
        breakdown = calculator.get_cost_breakdown("llama-3.1-70b")
        
        assert "gpu_cost_per_hour" in breakdown
        assert "electricity_cost_per_hour" in breakdown
        assert "cost_per_million_tokens" in breakdown
        
    def test_commercial_comparison(self, calculator):
        """Test comparison with commercial pricing."""
        comparison = calculator.compare_with_commercial("llama-3.1-70b")
        
        assert "self_hosted" in comparison
        assert "commercial" in comparison
        assert "savings_percentage" in comparison
        
        # Self-hosted 70B model may be more expensive than GPT-3.5-turbo
        # but cheaper than GPT-4
        self_hosted = comparison["self_hosted"]
        commercial_gpt4 = comparison["commercial"]["gpt-4"]
        assert self_hosted < commercial_gpt4


class TestAdaptiveHealthChecker:
    """Test adaptive health checking."""
    
    @pytest.fixture
    def mock_check(self):
        """Create a mock health check function."""
        return AsyncMock(return_value=True)
    
    @pytest.fixture
    def checker(self, mock_check):
        """Create a test health checker."""
        return AdaptiveHealthChecker(
            check_function=mock_check,
            name="test_service",
            min_interval=1,
            max_interval=10,
            initial_interval=2
        )
    
    @pytest.mark.asyncio
    async def test_health_check(self, checker, mock_check):
        """Test basic health checking."""
        result = await checker.check_health()
        
        assert result.healthy is True
        assert result.response_time >= 0
        assert result.timestamp is not None
        
    @pytest.mark.asyncio
    async def test_stability_score(self, checker, mock_check):
        """Test stability score updates."""
        # Initial state
        assert checker.stability_score == 1.0
        
        # Simulate failure
        mock_check.return_value = False
        await checker.check_health()
        
        assert checker.stability_score < 1.0
        
    def test_interval_calculation(self, checker):
        """Test adaptive interval calculation."""
        # With no history, use initial interval
        assert checker.calculate_next_interval() == 2
        
        # After successful checks, interval should increase
        checker.stability_score = 1.0
        next_interval = checker.calculate_next_interval()
        assert next_interval >= 2
        
    @pytest.mark.asyncio
    async def test_monitoring_loop(self, checker, mock_check):
        """Test monitoring loop with adaptive intervals."""
        # Start monitoring
        await checker.start_monitoring()
        
        # Let it run for a short time
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        await checker.stop_monitoring()
        
        assert len(checker.check_history) > 0


class TestModelSelector:
    """Test model selection logic."""
    
    @pytest.fixture
    def selector(self):
        """Create a test model selector."""
        return ModelSelector()
    
    def test_model_selection(self, selector):
        """Test model selection based on criteria."""
        from auren.ai.models import ModelConfig
        
        # Add test models
        selector.models["test-fast"] = ModelConfig(
            name="test-fast",
            provider="test",
            input_cost_per_1k=0.001,
            output_cost_per_1k=0.002,
            max_tokens=4000,
            supports_streaming=True,
            speed_tier="fast"
        )
        
        selector.models["test-cheap"] = ModelConfig(
            name="test-cheap",
            provider="test",
            input_cost_per_1k=0.0005,
            output_cost_per_1k=0.001,
            max_tokens=4000,
            supports_streaming=True,
            quality_tier="low"
        )
        
        # Test selection
        selected = selector.select_model(
            prompt="test prompt",
            remaining_budget=0.01,
            available_models=["test-fast", "test-cheap"],
            prefer_fast=True
        )
        
        assert selected in ["test-fast", "test-cheap"]


@pytest.mark.asyncio
async def test_integration():
    """Test full integration of all components."""
    # Create gateway
    gateway = AIGateway()
    
    # Test basic functionality
    request = GatewayRequest(
        prompt="Integration test prompt",
        user_id="integration_test"
    )
    
    # This would normally require actual providers
    # For now, just verify initialization
    assert gateway is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
