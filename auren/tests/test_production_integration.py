"""
Integration tests for the complete AUREN monitoring pipeline
Tests the flow from agent execution → events → Redis → WebSocket → S3
"""

import asyncio
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
import redis.asyncio as redis
import websockets

from auren.agents.monitored_specialist_agents import MonitoredNeuroscientistAgent
from auren.agents.monitored_orchestrator import ProductionAURENOrchestrator
from auren.realtime.hybrid_event_streamer import HybridEventStreamer
from auren.realtime.unified_dashboard_streamer import UnifiedDashboardStreamer
from auren.realtime.s3_event_archiver import S3EventArchiver
from auren.realtime.crewai_instrumentation import AURENStreamEvent, AURENEventType


class TestProductionIntegration:
    """
    End-to-end integration tests for the complete monitoring pipeline
    """
    
    @pytest.fixture
    async def redis_client(self):
        """Mock Redis client for testing"""
        client = AsyncMock()
        client.xadd = AsyncMock()
        client.xread = AsyncMock(return_value=[])
        client.xlen = AsyncMock(return_value=0)
        client.xtrim = AsyncMock()
        return client
    
    @pytest.fixture
    async def s3_client(self):
        """Mock S3 client for testing"""
        client = Mock()
        client.put_object = AsyncMock()
        return client
    
    @pytest.fixture
    async def hybrid_streamer(self, redis_client):
        """Create hybrid event streamer"""
        streamer = HybridEventStreamer(redis_url="redis://localhost:6379")
        streamer.redis_client = redis_client
        return streamer
    
    @pytest.fixture
    async def dashboard_streamer(self, redis_client):
        """Create dashboard streamer"""
        streamer = UnifiedDashboardStreamer(redis_url="redis://localhost:6379")
        streamer.redis_client = redis_client
        return streamer
    
    @pytest.fixture
    async def s3_archiver(self, s3_client, redis_client):
        """Create S3 archiver"""
        archiver = S3EventArchiver(
            s3_client=s3_client,
            redis_client=redis_client,
            bucket_name="test-auren-events"
        )
        return archiver
    
    @pytest.mark.asyncio
    async def test_critical_event_flow(self, hybrid_streamer, redis_client):
        """Test that critical events flow immediately through the pipeline"""
        # Create a critical event (agent execution)
        event = AURENStreamEvent(
            event_id="test-001",
            event_type=AURENEventType.AGENT_EXECUTION_STARTED,
            timestamp=datetime.now(timezone.utc),
            session_id="session-123",
            agent_id="neuroscientist",
            metadata={
                "user_query": "Analyze my HRV patterns",
                "biometric_context": {"hrv": 45, "stress_level": "moderate"}
            }
        )
        
        # Stream the event
        await hybrid_streamer.stream_event(event)
        
        # Verify immediate Redis write for critical events
        redis_client.xadd.assert_called_once()
        call_args = redis_client.xadd.call_args
        assert "auren:events:critical" in call_args[0]
        
    @pytest.mark.asyncio
    async def test_operational_event_batching(self, hybrid_streamer, redis_client):
        """Test that operational events are batched correctly"""
        # Create multiple operational events
        for i in range(30):
            event = AURENStreamEvent(
                event_id=f"test-op-{i}",
                event_type=AURENEventType.TOOL_USAGE,
                timestamp=datetime.now(timezone.utc),
                session_id="session-123",
                agent_id="neuroscientist",
                metadata={"tool": "biometric_analyzer", "tokens": 150}
            )
            await hybrid_streamer.stream_event(event)
        
        # Should not have flushed yet (buffer limit is 50)
        assert redis_client.xadd.call_count == 0
        
        # Add 20 more to trigger flush
        for i in range(30, 50):
            event = AURENStreamEvent(
                event_id=f"test-op-{i}",
                event_type=AURENEventType.TOOL_USAGE,
                timestamp=datetime.now(timezone.utc),
                session_id="session-123",
                agent_id="neuroscientist",
                metadata={"tool": "memory_access", "tokens": 100}
            )
            await hybrid_streamer.stream_event(event)
        
        # Now should have flushed
        await asyncio.sleep(0.1)  # Allow async flush
        assert redis_client.xadd.call_count == 1
        
    @pytest.mark.asyncio
    async def test_dashboard_subscription_filtering(self, dashboard_streamer):
        """Test that dashboard clients receive only subscribed events"""
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.recv = AsyncMock(return_value=json.dumps({
            "tiers": ["critical", "operational"],
            "agents": ["neuroscientist"],
            "rate_limit": 50
        }))
        mock_websocket.send = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        # Create test events
        critical_event = {
            "event_id": "test-crit-1",
            "event_type": "agent_execution_completed",
            "tier": "critical",
            "agent_id": "neuroscientist",
            "data": {"result": "Analysis complete"}
        }
        
        analytical_event = {
            "event_id": "test-anal-1",
            "event_type": "performance_metrics",
            "tier": "analytical",
            "agent_id": "neuroscientist",
            "data": {"cpu_usage": 45.2}
        }
        
        # Test filtering
        connection_id = "test-conn-1"
        config = {
            "tiers": ["critical", "operational"],
            "agents": ["neuroscientist"],
            "rate_limit": 50
        }
        
        # Critical event should pass filter
        assert dashboard_streamer._should_send_to_client(critical_event, config)
        
        # Analytical event should not pass filter
        assert not dashboard_streamer._should_send_to_client(analytical_event, config)
    
    @pytest.mark.asyncio
    async def test_s3_archival_partitioning(self, s3_archiver, s3_client):
        """Test that events are correctly partitioned in S3"""
        # Create events for different tiers
        events = [
            {
                "event_id": "arch-1",
                "tier": "critical",
                "timestamp": "2024-01-15T10:30:00Z",
                "data": {"test": "critical"}
            },
            {
                "event_id": "arch-2", 
                "tier": "operational",
                "timestamp": "2024-01-15T10:31:00Z",
                "data": {"test": "operational"}
            }
        ]
        
        # Archive events
        await s3_archiver._write_to_s3(events, "critical")
        
        # Verify S3 write with correct partitioning
        s3_client.put_object.assert_called_once()
        call_args = s3_client.put_object.call_args
        
        # Check the key includes proper partitioning
        key = call_args[1]["Key"]
        assert "year=2024" in key
        assert "month=01" in key
        assert "day=15" in key
        assert "tier=critical" in key
        assert key.endswith(".json.gz")
    
    @pytest.mark.asyncio
    async def test_end_to_end_monitoring_flow(
        self, 
        hybrid_streamer, 
        dashboard_streamer,
        s3_archiver,
        redis_client
    ):
        """Test complete flow from agent execution to S3 archival"""
        # Step 1: Agent generates event
        agent_event = AURENStreamEvent(
            event_id="e2e-test-1",
            event_type=AURENEventType.HYPOTHESIS_FORMED,
            timestamp=datetime.now(timezone.utc),
            session_id="e2e-session",
            agent_id="neuroscientist",
            metadata={
                "hypothesis": "User shows signs of overtraining",
                "confidence": 0.85,
                "evidence": ["elevated RHR", "decreased HRV", "poor sleep"]
            }
        )
        
        # Step 2: Event flows through hybrid streamer
        await hybrid_streamer.stream_event(agent_event)
        
        # Step 3: Verify Redis write
        assert redis_client.xadd.called
        redis_call = redis_client.xadd.call_args
        assert "auren:events:critical" in redis_call[0]
        
        # Step 4: Simulate dashboard reading from Redis
        mock_redis_data = [(
            b"auren:events:critical",
            [(b"123-0", {
                b"event_id": b"e2e-test-1",
                b"event_type": b"hypothesis_formed",
                b"tier": b"critical",
                b"agent_id": b"neuroscientist",
                b"data": json.dumps(agent_event.to_dict()).encode()
            })]
        )]
        
        redis_client.xread.return_value = mock_redis_data
        
        # Step 5: Process for archival
        await s3_archiver._process_stream_for_archival("critical", 1)
        
        # Verify the complete flow
        assert redis_client.xread.called
        assert redis_client.xtrim.called  # Cleanup after archival
    
    @pytest.mark.asyncio 
    async def test_orchestrator_session_management(self):
        """Test that orchestrator properly manages sessions and biometric context"""
        orchestrator = ProductionAURENOrchestrator()
        
        # Mock biometric data source
        mock_biometric_data = {
            "hrv": 55,
            "resting_hr": 58,
            "sleep_score": 85,
            "stress_level": "low",
            "recovery_score": 92
        }
        
        with patch.object(
            orchestrator, 
            '_fetch_biometric_data',
            return_value=mock_biometric_data
        ):
            # Start a session
            session_id = await orchestrator.start_session("user-123")
            assert session_id in orchestrator.active_sessions
            
            # Verify biometric context is cached
            context = await orchestrator._prepare_shared_context("user-123")
            assert context["biometrics"] == mock_biometric_data
            
            # Second call should use cache
            with patch.object(orchestrator, '_fetch_biometric_data') as mock_fetch:
                context2 = await orchestrator._prepare_shared_context("user-123")
                mock_fetch.assert_not_called()  # Should use cache
                assert context2 == context
    
    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, hybrid_streamer):
        """Test that performance metrics are properly tracked"""
        # Create a performance event
        perf_event = AURENStreamEvent(
            event_id="perf-1",
            event_type=AURENEventType.PERFORMANCE_METRICS,
            timestamp=datetime.now(timezone.utc),
            session_id="perf-session",
            agent_id="neuroscientist",
            metadata={
                "operation": "biometric_analysis",
                "duration_ms": 1250,
                "memory_mb": 156.7,
                "tokens_used": 2500,
                "cost_usd": 0.075
            }
        )
        
        # Verify it's classified as analytical
        classification = hybrid_streamer._classify_event(perf_event)
        assert classification == "analytical"
        
        # Verify batching behavior
        await hybrid_streamer.stream_event(perf_event)
        assert len(hybrid_streamer.analytical_buffer) == 1


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"]) 