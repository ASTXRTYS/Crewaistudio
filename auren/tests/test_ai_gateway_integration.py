"""
Integration tests for AI Gateway with real services.

These tests verify the AI Gateway works correctly with actual services.
Run with: pytest tests/test_ai_gateway_integration.py -v --integration

Tests cover:
1. Real OpenAI API calls (with test API key)
2. Redis connection and failover
3. Circuit breaker behavior under load
4. Token tracking accuracy
5. Cost calculation verification
"""

import pytest
import asyncio
import os
import time
from unittest.mock import patch
import redis.asyncio as redis

from src.auren.ai import (
    AIGateway,
    GatewayRequest,
    load_config,
    ResilientTokenTracker
)


# Mark all tests as integration tests
pytestmark = pytest.mark.integration


class TestAIGatewayIntegration:
    """Integration tests for the AI Gateway."""
    
    @pytest.fixture
    async def gateway(self):
        """Create a gateway with real configuration."""
        # Use test configuration
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY_TEST", "sk-test"),
            "REDIS_URL": os.getenv("REDIS_URL_TEST", "redis://localhost:6379/15"),
            "DAILY_BUDGET_LIMIT": "100.0"
        }):
            gateway = AIGateway()
            yield gateway
            # Cleanup
            await gateway.shutdown()
    
    @pytest.fixture
    async def redis_client(self):
        """Create a Redis client for testing."""
        client = await redis.from_url(
            os.getenv("REDIS_URL_TEST", "redis://localhost:6379/15")
        )
        yield client
        await client.flushdb()  # Clean test database
        await client.close()
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY_TEST"),
        reason="OpenAI API key not configured for testing"
    )
    async def test_openai_integration(self, gateway):
        """Test real OpenAI API integration."""
        request = GatewayRequest(
            prompt="Say 'test successful' and nothing else.",
            user_id="test_user",
            max_tokens=10
        )
        
        response = await gateway.complete(request)
        
        assert response.content.lower().strip() in [
            "test successful", "test successful.", "test successful!"
        ]
        assert response.total_tokens > 0
        assert response.model_used == "gpt-3.5-turbo"
        assert response.cost > 0
    
    @pytest.mark.skipif(
        not os.getenv("REDIS_URL_TEST"),
        reason="Redis not configured for testing"
    )
    async def test_redis_token_tracking(self, gateway, redis_client):
        """Test Redis-based token tracking."""
        user_id = "test_user_redis"
        
        # Track some usage
        await gateway.token_tracker.track_usage(
            user_id=user_id,
            model="gpt-3.5-turbo",
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.0002
        )
        
        # Verify tracking
        stats = await gateway.token_tracker.get_user_stats(user_id)
        assert stats["today"]["used"] == pytest.approx(0.0002, rel=1e-4)
        
        # Verify Redis storage
        daily_key = f"daily:{user_id}:{time.strftime('%Y-%m-%d')}"
        stored_value = await redis_client.hget(daily_key, "used")
        assert float(stored_value) == pytest.approx(0.0002, rel=1e-4)
    
    async def test_circuit_breaker_real_failure(self, gateway):
        """Test circuit breaker with real network failures."""
        # Mock a provider to fail
        original_complete = gateway.providers.get("openai", None)
        
        if original_complete:
            fail_count = 0
            
            async def failing_complete(*args, **kwargs):
                nonlocal fail_count
                fail_count += 1
                if fail_count < 5:
                    raise Exception("Network error")
                return await original_complete.complete(*args, **kwargs)
            
            gateway.providers["openai"].complete = failing_complete
            
            # First requests should fail
            for _ in range(3):
                with pytest.raises(Exception):
                    await gateway.complete(GatewayRequest(
                        prompt="test",
                        user_id="test_user"
                    ))
            
            # Circuit should be open
            breaker = gateway.circuit_breakers.get("openai")
            if breaker:
                assert breaker.state == "open"
    
    async def test_concurrent_requests(self, gateway):
        """Test handling multiple concurrent requests."""
        requests = [
            GatewayRequest(
                prompt=f"Return the number {i}",
                user_id=f"user_{i % 3}",  # 3 different users
                max_tokens=10
            )
            for i in range(10)
        ]
        
        # Execute concurrently
        responses = await asyncio.gather(
            *[gateway.complete(req) for req in requests],
            return_exceptions=True
        )
        
        # Verify responses
        successful = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful) >= 5  # At least half should succeed
        
        # Verify each user's budget was tracked
        for i in range(3):
            stats = await gateway.token_tracker.get_user_stats(f"user_{i}")
            if stats and "today" in stats:
                assert stats["today"]["used"] > 0
    
    async def test_budget_enforcement_integration(self, gateway):
        """Test budget enforcement with real tracking."""
        user_id = "budget_test_user"
        
        # Set a very low budget
        await gateway.set_user_budget(user_id, 0.001)
        
        # First request should succeed
        response = await gateway.complete(GatewayRequest(
            prompt="Hi",
            user_id=user_id,
            max_tokens=5
        ))
        assert response.content
        
        # Subsequent requests should fail due to budget
        with pytest.raises(ValueError, match="budget"):
            await gateway.complete(GatewayRequest(
                prompt="This should fail due to budget",
                user_id=user_id
            ))
    
    async def test_failover_to_self_hosted(self, gateway):
        """Test failover from OpenAI to self-hosted models."""
        # This test requires both OpenAI and a self-hosted model
        if not gateway.config.llama_endpoint:
            pytest.skip("Self-hosted model not configured")
        
        # Force OpenAI to fail
        if "openai" in gateway.providers:
            gateway.providers["openai"].health_check = asyncio.coroutine(
                lambda: False
            )
        
        # Request should failover to self-hosted
        response = await gateway.complete(GatewayRequest(
            prompt="Test failover",
            user_id="test_user"
        ))
        
        assert response.model_used in ["llama-3.1-70b", "meditron-70b"]
    
    async def test_cost_calculation_accuracy(self, gateway):
        """Test cost calculations match actual usage."""
        user_id = "cost_test_user"
        
        # Make a request with known token counts
        response = await gateway.complete(GatewayRequest(
            prompt="Count to five: ",  # ~4 tokens
            user_id=user_id,
            max_tokens=20  # Enough for "1, 2, 3, 4, 5"
        ))
        
        # Verify cost calculation
        model_config = gateway.model_selector.models.get(response.model_used)
        if model_config:
            expected_cost = model_config.estimate_cost(
                response.prompt_tokens,
                response.completion_tokens
            )
            assert response.cost == pytest.approx(expected_cost, rel=0.01)
        
        # Verify tracked cost matches
        stats = await gateway.token_tracker.get_user_stats(user_id)
        if stats and "today" in stats:
            assert stats["today"]["used"] == pytest.approx(response.cost, rel=0.01)


class TestEndToEndScenarios:
    """End-to-end scenarios testing complete user journeys."""
    
    @pytest.fixture
    async def gateway(self):
        """Create a gateway for E2E tests."""
        gateway = AIGateway()
        yield gateway
        await gateway.shutdown()
    
    async def test_user_journey_medical_consultation(self, gateway):
        """Test a complete medical consultation scenario."""
        user_id = "medical_user"
        
        # User asks about symptoms
        response1 = await gateway.complete(GatewayRequest(
            prompt="I have a headache and fatigue. What could it be?",
            user_id=user_id,
            model_preference="high_quality"
        ))
        
        assert response1.content
        assert "consult" in response1.content.lower() or "doctor" in response1.content.lower()
        
        # Follow-up question
        response2 = await gateway.complete(GatewayRequest(
            prompt="What are common causes of fatigue?",
            user_id=user_id
        ))
        
        assert response2.content
        
        # Verify conversation cost
        stats = await gateway.token_tracker.get_user_stats(user_id)
        if stats and "today" in stats:
            total_cost = response1.cost + response2.cost
            assert stats["today"]["used"] == pytest.approx(total_cost, rel=0.01)
    
    async def test_high_load_scenario(self, gateway):
        """Test system behavior under high load."""
        # Simulate 50 concurrent users
        users = [f"load_test_user_{i}" for i in range(50)]
        
        async def user_session(user_id: str):
            """Simulate a user session."""
            for j in range(3):  # Each user makes 3 requests
                try:
                    await gateway.complete(GatewayRequest(
                        prompt=f"Question {j} from {user_id}",
                        user_id=user_id,
                        max_tokens=10
                    ))
                    await asyncio.sleep(0.1)  # Small delay between requests
                except Exception:
                    pass  # Some failures expected under load
        
        # Run all user sessions concurrently
        start_time = time.time()
        await asyncio.gather(
            *[user_session(user_id) for user_id in users],
            return_exceptions=True
        )
        duration = time.time() - start_time
        
        # System should handle load reasonably
        assert duration < 30  # Should complete within 30 seconds
        
        # Check circuit breakers didn't all open
        open_breakers = sum(
            1 for cb in gateway.circuit_breakers.values()
            if cb.state == "open"
        )
        assert open_breakers < len(gateway.circuit_breakers)  # At least one should work


# Test configuration validation
def test_configuration_validation():
    """Test configuration validation catches errors."""
    with patch.dict(os.environ, {
        "REDIS_URL": "invalid://url",
        "DAILY_BUDGET_LIMIT": "-10"
    }):
        with pytest.raises(ValueError):
            load_config()


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration"]) 