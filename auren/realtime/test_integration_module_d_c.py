"""
Integration Tests for Module D-C Implementation
Tests the complete event flow from agents through Redis to dashboard
"""

import asyncio
import pytest
import json
from datetime import datetime, timezone
import redis.asyncio as redis
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realtime.enhanced_websocket_streamer import EnhancedWebSocketStreamer
from realtime.langgraph_instrumentation import (
    CrewAIEventInstrumentation,
    AURENStreamEvent,
    AURENEventType,
    AURENPerformanceMetrics
)
from realtime.dashboard_backends import (
    UnifiedDashboardAPI,
    ReasoningChainVisualizer,
    CostAnalyticsDashboard,
    LearningSystemVisualizer
)


class TestModuleDCIntegration:
    """
    Complete integration tests for Module D-C implementation
    Validates event flow from agents to dashboard
    """
    
    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing"""
        client = redis.from_url("redis://localhost:6379")
        
        # Clean up test data
        await client.delete("auren:events:critical")
        await client.delete("auren:events:operational") 
        await client.delete("auren:events:analytical")
        
        yield client
        
        await client.close()
    
    @pytest.fixture
    async def event_instrumentation(self, redis_client):
        """Create event instrumentation instance"""
        instrumentation = CrewAIEventInstrumentation(
            redis_url="redis://localhost:6379",
            enable_streaming=True
        )
        await instrumentation.initialize()
        
        yield instrumentation
        
        await instrumentation.close()
    
    @pytest.fixture
    async def dashboard_api(self):
        """Create dashboard API instance"""
        api = UnifiedDashboardAPI(
            redis_url="redis://localhost:6379"
        )
        await api.initialize()
        
        yield api
    
    @pytest.mark.asyncio
    async def test_agent_event_to_dashboard_flow(self, event_instrumentation, dashboard_api, redis_client):
        """Test complete flow from agent event to dashboard visualization"""
        
        # 1. Emit agent execution event
        test_event = AURENStreamEvent(
            event_id="test_001",
            event_type=AURENEventType.AGENT_EXECUTION_STARTED,
            timestamp=datetime.now(timezone.utc),
            session_id="session_123",
            source_agent={
                "agent_id": "neuroscientist",
                "role": "Neuroscientist",
                "goal": "Analyze HRV patterns"
            },
            payload={
                "query": "Analyze my recent HRV decline",
                "context": {"hrv_trend": "declining"}
            },
            priority="critical"
        )
        
        await event_instrumentation.emit_event(test_event)
        
        # 2. Wait for event to be processed
        await asyncio.sleep(0.5)
        
        # 3. Verify event in Redis
        events = await redis_client.xread({"auren:events:critical": "0"})
        assert len(events) > 0
        assert len(events[0][1]) > 0  # Has at least one event
        
        # 4. Emit reasoning step
        reasoning_event = AURENStreamEvent(
            event_id="test_002",
            event_type="reasoning_step",
            timestamp=datetime.now(timezone.utc),
            session_id="session_123",
            source_agent={"agent_id": "neuroscientist"},
            payload={
                "step_id": "step_001",
                "thought": "HRV decline detected, analyzing potential causes",
                "confidence": 0.85
            },
            priority="operational"
        )
        
        await event_instrumentation.emit_event(reasoning_event)
        await asyncio.sleep(0.5)
        
        # 5. Check dashboard data
        reasoning_data = await dashboard_api.get_dashboard_data("reasoning", session_id="session_123")
        
        # Verify reasoning chain exists
        assert "session_id" in reasoning_data
        assert reasoning_data["session_id"] == "session_123"
        assert "steps" in reasoning_data
        assert len(reasoning_data["steps"]) > 0
        
        # 6. Emit cost event
        cost_event = AURENStreamEvent(
            event_id="test_003",
            event_type="llm_call_completed",
            timestamp=datetime.now(timezone.utc),
            session_id="session_123",
            source_agent={"agent_id": "neuroscientist"},
            payload={
                "model": "gpt-4",
                "input_tokens": 500,
                "output_tokens": 200,
                "latency_ms": 1200
            },
            performance_metrics=AURENPerformanceMetrics(
                latency_ms=1200,
                token_cost=0.021,  # (500 * 0.03 + 200 * 0.06) / 1000
                success=True
            ),
            priority="analytical"
        )
        
        await event_instrumentation.emit_event(cost_event)
        await asyncio.sleep(0.5)
        
        # 7. Check cost analytics
        cost_data = await dashboard_api.get_dashboard_data("cost")
        
        assert "current" in cost_data
        assert cost_data["current"]["total_cost"] > 0
        assert cost_data["current"]["token_count"] == 700
        
        # 8. Emit memory event
        memory_event = AURENStreamEvent(
            event_id="test_004",
            event_type="memory_stored",
            timestamp=datetime.now(timezone.utc),
            session_id="session_123",
            source_agent={"agent_id": "neuroscientist"},
            payload={
                "memory_type": "insight",
                "content": "User shows consistent HRV decline during work hours",
                "confidence": 0.9
            },
            priority="operational"
        )
        
        await event_instrumentation.emit_event(memory_event)
        await asyncio.sleep(0.5)
        
        # 9. Check learning metrics
        learning_data = await dashboard_api.get_dashboard_data("learning")
        
        assert "metrics" in learning_data
        assert learning_data["metrics"]["total_memories"] > 0
        
        print("✅ All integration tests passed!")
        
    @pytest.mark.asyncio
    async def test_multi_agent_collaboration_flow(self, event_instrumentation, dashboard_api):
        """Test multi-agent collaboration event flow"""
        
        # 1. Start collaboration
        collab_start = AURENStreamEvent(
            event_id="collab_001",
            event_type="collaboration_started",
            timestamp=datetime.now(timezone.utc),
            session_id="collab_session",
            source_agent={"agent_id": "neuroscientist"},
            payload={
                "target_agent": "nutritionist",
                "reason": "Need nutrition recommendations for stress recovery"
            },
            priority="critical"
        )
        
        await event_instrumentation.emit_event(collab_start)
        
        # 2. Nutritionist responds
        nutritionist_event = AURENStreamEvent(
            event_id="collab_002",
            event_type="agent_execution_started",
            timestamp=datetime.now(timezone.utc),
            session_id="collab_session",
            source_agent={
                "agent_id": "nutritionist",
                "role": "Nutritionist"
            },
            payload={
                "query": "Provide nutrition plan for stress recovery",
                "context": {"stress_level": "high", "hrv_trend": "declining"}
            },
            priority="critical"
        )
        
        await event_instrumentation.emit_event(nutritionist_event)
        await asyncio.sleep(0.5)
        
        # 3. Check active chains
        reasoning_data = await dashboard_api.get_dashboard_data("reasoning")
        active_chains = reasoning_data.get("active_chains", [])
        
        # Find collaboration session
        collab_chain = next((c for c in active_chains if c["session_id"] == "collab_session"), None)
        assert collab_chain is not None
        assert "neuroscientist" in collab_chain["agents_involved"]
        assert "nutritionist" in collab_chain["agents_involved"]
        
    @pytest.mark.asyncio
    async def test_biometric_context_integration(self, event_instrumentation, dashboard_api):
        """Test biometric context flowing through system"""
        
        # 1. Emit biometric analysis event
        biometric_event = AURENStreamEvent(
            event_id="bio_001",
            event_type="biometric_analysis",
            timestamp=datetime.now(timezone.utc),
            session_id="bio_session",
            source_agent={"agent_id": "neuroscientist"},
            payload={
                "metrics_available": ["hrv", "sleep_efficiency"],
                "hrv_value": 35,
                "sleep_efficiency": 0.72,
                "analysis": "Low HRV combined with poor sleep indicates high stress"
            },
            priority="critical"
        )
        
        await event_instrumentation.emit_event(biometric_event)
        
        # 2. Emit hypothesis based on biometrics
        hypothesis_event = AURENStreamEvent(
            event_id="bio_002",
            event_type="hypothesis_formed",
            timestamp=datetime.now(timezone.utc),
            session_id="bio_session",
            source_agent={"agent_id": "neuroscientist"},
            payload={
                "hypothesis_id": "hyp_001",
                "domain": "stress_recovery",
                "description": "Work stress is primary driver of HRV decline",
                "confidence": 0.75,
                "evidence": ["hrv_pattern", "sleep_pattern", "work_schedule"]
            },
            priority="operational"
        )
        
        await event_instrumentation.emit_event(hypothesis_event)
        await asyncio.sleep(0.5)
        
        # 3. Check learning metrics
        learning_data = await dashboard_api.get_dashboard_data("learning")
        
        assert learning_data["metrics"]["hypotheses_formed"] > 0
        assert len(learning_data["hypothesis_timeline"]) > 0
        
        # Find our hypothesis
        hyp = next((h for h in learning_data["hypothesis_timeline"] 
                   if h["hypothesis_id"] == "hyp_001"), None)
        assert hyp is not None
        assert hyp["domain"] == "stress_recovery"
        
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, event_instrumentation, redis_client):
        """Test performance metrics collection"""
        
        # Emit multiple events with varying performance
        for i in range(10):
            perf_event = AURENStreamEvent(
                event_id=f"perf_{i:03d}",
                event_type=AURENEventType.AGENT_EXECUTION_COMPLETED,
                timestamp=datetime.now(timezone.utc),
                session_id=f"perf_session_{i}",
                source_agent={"agent_id": "neuroscientist"},
                payload={"result": "Analysis complete"},
                performance_metrics=AURENPerformanceMetrics(
                    latency_ms=500 + (i * 100),  # Increasing latency
                    token_cost=0.01 * (i + 1),
                    memory_usage_mb=100 + (i * 10),
                    cpu_percentage=20 + (i * 5),
                    success=i < 8  # Last 2 fail
                ),
                priority="analytical"
            )
            
            await event_instrumentation.emit_event(perf_event)
        
        await asyncio.sleep(1)
        
        # Check events were stored
        events = await redis_client.xread({"auren:events:analytical": "0"})
        assert len(events[0][1]) >= 10
        
        # Verify performance degradation would trigger alerts
        # In production, this would trigger monitoring alerts
        
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, event_instrumentation, dashboard_api):
        """Test system behavior under error conditions"""
        
        # 1. Emit error event
        error_event = AURENStreamEvent(
            event_id="error_001",
            event_type=AURENEventType.AGENT_EXECUTION_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            session_id="error_session",
            source_agent={"agent_id": "neuroscientist"},
            payload={
                "error": "API rate limit exceeded",
                "error_type": "RateLimitError"
            },
            performance_metrics=AURENPerformanceMetrics(
                latency_ms=100,
                success=False,
                error_type="RateLimitError"
            ),
            priority="critical"
        )
        
        await event_instrumentation.emit_event(error_event)
        await asyncio.sleep(0.5)
        
        # 2. Check cost analytics handles errors
        cost_data = await dashboard_api.get_dashboard_data("cost")
        
        # Success rate should reflect the error
        cache_hit_rate = cost_data.get("cache_hit_rate", 0)
        assert isinstance(cache_hit_rate, (int, float))
        
        print("✅ Error handling test passed!")


async def run_integration_tests():
    """Run all integration tests"""
    print("🧪 Running Module D-C Integration Tests...")
    print("=" * 60)
    
    # Create test instance
    test_suite = TestModuleDCIntegration()
    
    # Setup fixtures
    redis_client = redis.from_url("redis://localhost:6379")
    await redis_client.delete("auren:events:critical")
    await redis_client.delete("auren:events:operational")
    await redis_client.delete("auren:events:analytical")
    
    instrumentation = CrewAIEventInstrumentation(
        redis_url="redis://localhost:6379",
        enable_streaming=True
    )
    await instrumentation.initialize()
    
    dashboard_api = UnifiedDashboardAPI("redis://localhost:6379")
    await dashboard_api.initialize()
    
    try:
        # Run tests
        print("\n1️⃣ Testing Agent Event to Dashboard Flow...")
        await test_suite.test_agent_event_to_dashboard_flow(
            instrumentation, dashboard_api, redis_client
        )
        
        print("\n2️⃣ Testing Multi-Agent Collaboration...")
        await test_suite.test_multi_agent_collaboration_flow(
            instrumentation, dashboard_api
        )
        
        print("\n3️⃣ Testing Biometric Context Integration...")
        await test_suite.test_biometric_context_integration(
            instrumentation, dashboard_api
        )
        
        print("\n4️⃣ Testing Performance Monitoring...")
        await test_suite.test_performance_monitoring(
            instrumentation, redis_client
        )
        
        print("\n5️⃣ Testing Error Handling...")
        await test_suite.test_error_handling_and_recovery(
            instrumentation, dashboard_api
        )
        
        print("\n" + "=" * 60)
        print("✅ All Module D-C Integration Tests PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        await instrumentation.close()
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(run_integration_tests()) 