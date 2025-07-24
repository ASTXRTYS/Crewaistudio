"""
Test Performance Optimizer Implementation
Verifies event batching, circuit breaker, and performance metrics
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from collections import deque

from auren.realtime.performance_optimizer import (
    EventBatcher,
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    PerformanceOptimizer,
    LoadTestGenerator,
    BatchMetrics,
    PerformanceStats
)


@pytest.fixture
def mock_base_streamer():
    """Create mock base streamer"""
    streamer = AsyncMock()
    streamer.stream_event.return_value = True
    return streamer


@pytest.fixture
def event_batcher():
    """Create event batcher"""
    return EventBatcher(
        max_batch_size=5,  # Small for testing
        max_wait_time_ms=50  # Short timeout for testing
    )


@pytest.fixture
def circuit_breaker():
    """Create circuit breaker"""
    return CircuitBreaker(
        failure_threshold=3,  # Low threshold for testing
        recovery_timeout_seconds=1  # Short recovery for testing
    )


@pytest.fixture
def performance_optimizer(mock_base_streamer):
    """Create performance optimizer"""
    return PerformanceOptimizer(
        base_streamer=mock_base_streamer,
        batch_size=5,
        batch_timeout_ms=50,
        circuit_failure_threshold=3,
        circuit_recovery_seconds=1
    )


class TestEventBatcher:
    
    @pytest.mark.asyncio
    async def test_batch_size_limit(self, event_batcher):
        """Test batching up to size limit"""
        
        flushed_batches = []
        
        async def capture_flush(batch, reason):
            flushed_batches.append((batch.copy(), reason))
        
        event_batcher.flush_callback = capture_flush
        
        # Add events up to batch size
        for i in range(5):
            await event_batcher.add_event(f"event_{i}")
        
        # Should have flushed due to size
        assert len(flushed_batches) == 1
        batch, reason = flushed_batches[0]
        assert len(batch) == 5
        assert reason == "size_limit"
        assert event_batcher.total_batches_sent == 1
    
    @pytest.mark.asyncio
    async def test_batch_timeout(self, event_batcher):
        """Test batching with timeout"""
        
        flushed_batches = []
        
        async def capture_flush(batch, reason):
            flushed_batches.append((batch.copy(), reason))
        
        event_batcher.flush_callback = capture_flush
        
        # Add events less than batch size
        for i in range(3):
            await event_batcher.add_event(f"event_{i}")
        
        # Wait for timeout
        await asyncio.sleep(0.06)  # 60ms > 50ms timeout
        
        # Should have flushed due to timeout
        assert len(flushed_batches) == 1
        batch, reason = flushed_batches[0]
        assert len(batch) == 3
        assert reason == "timeout"
    
    @pytest.mark.asyncio
    async def test_force_flush(self, event_batcher):
        """Test force flushing partial batch"""
        
        flushed_batches = []
        
        async def capture_flush(batch, reason):
            flushed_batches.append((batch.copy(), reason))
        
        event_batcher.flush_callback = capture_flush
        
        # Add partial batch
        await event_batcher.add_event("event_1")
        await event_batcher.add_event("event_2")
        
        # Force flush
        await event_batcher.force_flush()
        
        assert len(flushed_batches) == 1
        batch, reason = flushed_batches[0]
        assert len(batch) == 2
        assert reason == "forced"
    
    @pytest.mark.asyncio
    async def test_batch_metrics_collection(self, event_batcher):
        """Test metrics collection for batches"""
        
        async def mock_flush(batch, reason):
            pass  # Success
        
        event_batcher.flush_callback = mock_flush
        
        # Send multiple batches
        for batch_num in range(3):
            for i in range(5):
                await event_batcher.add_event(f"batch_{batch_num}_event_{i}")
            await asyncio.sleep(0.01)
        
        # Get metrics
        metrics = event_batcher.get_metrics()
        
        assert metrics["total_events"] == 15
        assert metrics["total_batches"] == 3
        assert metrics["avg_batch_size"] == 5.0
        assert metrics["batching_efficiency"] == 1.0  # 5/5 = 100%
        assert metrics["success_rate"] == 1.0
    
    @pytest.mark.asyncio
    async def test_concurrent_event_addition(self, event_batcher):
        """Test concurrent event addition"""
        
        flushed_count = 0
        
        async def count_flush(batch, reason):
            nonlocal flushed_count
            flushed_count += 1
        
        event_batcher.flush_callback = count_flush
        
        # Add events concurrently
        tasks = []
        for i in range(20):
            tasks.append(event_batcher.add_event(f"concurrent_event_{i}"))
        
        await asyncio.gather(*tasks)
        
        # Wait for any pending flushes
        await asyncio.sleep(0.1)
        
        # Should have flushed 4 batches (20 events / 5 batch size)
        assert flushed_count == 4
        assert event_batcher.total_events_batched == 20


class TestCircuitBreaker:
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_normal_operation(self, circuit_breaker):
        """Test circuit breaker in normal (closed) state"""
        
        async def successful_operation():
            return "success"
        
        # Should work normally
        result = await circuit_breaker.call(successful_operation)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.total_successes == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_trip_on_failures(self, circuit_breaker):
        """Test circuit breaker trips after threshold failures"""
        
        async def failing_operation():
            raise Exception("Test failure")
        
        # Fail up to threshold
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_operation)
        
        # Circuit should be open
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.trip_count == 1
        assert circuit_breaker.failure_count == 3
        
        # Next call should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.call(failing_operation)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, circuit_breaker):
        """Test circuit breaker recovery after timeout"""
        
        async def failing_operation():
            raise Exception("Test failure")
        
        async def successful_operation():
            return "success"
        
        # Trip the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_operation)
        
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)  # > 1 second recovery timeout
        
        # Should transition to half-open and allow test
        result = await circuit_breaker.call(successful_operation)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.HALF_OPEN
        
        # More successes should close circuit
        for i in range(2):
            await circuit_breaker.call(successful_operation)
        
        assert circuit_breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_failure(self, circuit_breaker):
        """Test circuit breaker re-opens on failure in half-open state"""
        
        async def failing_operation():
            raise Exception("Test failure")
        
        async def successful_operation():
            return "success"
        
        # Trip the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_operation)
        
        # Wait for recovery
        await asyncio.sleep(1.1)
        
        # One success to enter half-open
        await circuit_breaker.call(successful_operation)
        assert circuit_breaker.state == CircuitState.HALF_OPEN
        
        # Failure should re-open circuit
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_operation)
        
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.trip_count == 2
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_metrics(self, circuit_breaker):
        """Test circuit breaker metrics collection"""
        
        async def mixed_operation(should_fail):
            if should_fail:
                raise Exception("Test failure")
            return "success"
        
        # Mix of successes and failures
        await circuit_breaker.call(mixed_operation, False)  # Success
        with pytest.raises(Exception):
            await circuit_breaker.call(mixed_operation, True)  # Failure
        await circuit_breaker.call(mixed_operation, False)  # Success
        with pytest.raises(Exception):
            await circuit_breaker.call(mixed_operation, True)  # Failure
        
        metrics = circuit_breaker.get_metrics()
        
        assert metrics["current_state"] == "closed"
        assert metrics["total_calls"] == 4
        assert metrics["total_successes"] == 2
        assert metrics["total_failures"] == 2
        assert metrics["failure_rate"] == 0.5
        assert metrics["trip_count"] == 0  # Not tripped yet


class TestPerformanceOptimizer:
    
    @pytest.mark.asyncio
    async def test_optimizer_initialization(self, performance_optimizer):
        """Test optimizer initialization"""
        
        await performance_optimizer.initialize()
        
        assert performance_optimizer.batcher.max_batch_size == 5
        assert performance_optimizer.batcher.max_wait_time_ms == 50
        assert performance_optimizer.circuit_breaker.failure_threshold == 3
        assert performance_optimizer.stats_task is not None
        
        # Cleanup
        await performance_optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_event_streaming_with_batching(self, performance_optimizer, mock_base_streamer):
        """Test event streaming with batching"""
        
        await performance_optimizer.initialize()
        
        # Stream events
        for i in range(10):
            success = await performance_optimizer.stream_event(f"event_{i}")
            assert success
        
        # Force flush to ensure all events are sent
        await performance_optimizer.force_flush()
        
        # Verify events were batched and sent
        assert performance_optimizer.events_processed == 10
        assert performance_optimizer.batcher.total_batches_sent == 2  # 10 events / 5 batch size
        
        # Cleanup
        await performance_optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, performance_optimizer, mock_base_streamer):
        """Test circuit breaker protects against failures"""
        
        await performance_optimizer.initialize()
        
        # Make base streamer fail
        mock_base_streamer.stream_event.side_effect = Exception("Simulated failure")
        
        # Stream events that will fail
        for i in range(20):
            await performance_optimizer.stream_event(f"event_{i}")
        
        # Force flush to trigger failures
        await performance_optimizer.force_flush()
        
        # Wait a bit for circuit to trip
        await asyncio.sleep(0.1)
        
        # Circuit should be open after failures
        assert performance_optimizer.circuit_breaker.state == CircuitState.OPEN
        assert performance_optimizer.events_dropped > 0
        
        # Cleanup
        await performance_optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, performance_optimizer):
        """Test performance metrics collection"""
        
        await performance_optimizer.initialize()
        
        # Generate some activity
        for i in range(25):
            await performance_optimizer.stream_event(f"event_{i}")
        
        await performance_optimizer.force_flush()
        
        # Get metrics
        stats = performance_optimizer.get_performance_stats()
        
        assert stats.total_events == 25
        assert stats.total_batches == 5  # 25 events / 5 batch size
        assert stats.avg_batch_size == 5.0
        assert stats.batching_efficiency == 1.0
        assert stats.throughput_eps > 0
        assert stats.circuit_breaker_trips == 0
        assert stats.error_rate == 0.0
        
        # Cleanup
        await performance_optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_dashboard_metrics_format(self, performance_optimizer):
        """Test dashboard metrics formatting"""
        
        await performance_optimizer.initialize()
        
        # Generate activity
        for i in range(15):
            await performance_optimizer.stream_event(f"event_{i}")
        
        await asyncio.sleep(0.1)  # Let batches process
        
        # Get dashboard metrics
        metrics = performance_optimizer.get_dashboard_metrics()
        
        assert "performance_stats" in metrics
        assert "batching" in metrics
        assert "circuit_breaker" in metrics
        assert "throughput" in metrics
        assert "latency" in metrics
        
        # Verify batching metrics
        assert metrics["batching"]["efficiency"] >= 0
        assert metrics["batching"]["total_batches"] > 0
        
        # Verify circuit breaker metrics
        assert metrics["circuit_breaker"]["state"] == "closed"
        assert metrics["circuit_breaker"]["failure_rate"] == 0
        
        # Cleanup
        await performance_optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, performance_optimizer):
        """Test graceful shutdown with pending events"""
        
        await performance_optimizer.initialize()
        
        # Add events but don't wait for flush
        for i in range(3):
            await performance_optimizer.stream_event(f"pending_event_{i}")
        
        # Shutdown should flush pending events
        await performance_optimizer.shutdown()
        
        # All events should be processed
        assert performance_optimizer.events_processed == 3
        assert performance_optimizer.batcher.current_batch == []


class TestLoadTestGenerator:
    
    @pytest.mark.asyncio
    async def test_load_generation(self, performance_optimizer):
        """Test load test generator"""
        
        await performance_optimizer.initialize()
        
        # Create load generator
        load_generator = LoadTestGenerator(target_eps=100)  # 100 events/sec
        
        # Run short load test
        load_task = asyncio.create_task(
            load_generator.generate_load(performance_optimizer, duration_seconds=0.5)
        )
        
        await load_task
        
        # Should have generated approximately 50 events (100 eps * 0.5s)
        assert 40 <= load_generator.events_generated <= 60
        assert performance_optimizer.events_processed > 0
        
        # Cleanup
        await performance_optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_load_generator_stop(self):
        """Test stopping load generator"""
        
        load_generator = LoadTestGenerator(target_eps=1000)
        
        # Start generation in background
        optimizer = MagicMock()
        optimizer.stream_event = AsyncMock()
        
        load_task = asyncio.create_task(
            load_generator.generate_load(optimizer, duration_seconds=10)
        )
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Stop it
        load_generator.stop()
        
        # Wait for task to complete
        await load_task
        
        # Should have stopped early
        assert load_generator.running is False
        assert load_generator.events_generated > 0


@pytest.mark.integration
class TestPerformanceOptimizationIntegration:
    
    @pytest.mark.asyncio
    async def test_full_optimization_pipeline(self, mock_base_streamer):
        """Test complete optimization pipeline under load"""
        
        # Create optimizer with production-like settings
        optimizer = PerformanceOptimizer(
            base_streamer=mock_base_streamer,
            batch_size=50,
            batch_timeout_ms=100,
            circuit_failure_threshold=5,
            circuit_recovery_seconds=30
        )
        
        await optimizer.initialize()
        
        # Simulate mixed load
        success_count = 0
        for i in range(200):
            # Every 50th event, make the base streamer fail temporarily
            if i % 50 == 49:
                mock_base_streamer.stream_event.side_effect = Exception("Temporary failure")
            else:
                mock_base_streamer.stream_event.side_effect = None
                mock_base_streamer.stream_event.return_value = True
            
            success = await optimizer.stream_event(f"test_event_{i}")
            if success:
                success_count += 1
            
            # Small delay to simulate real timing
            await asyncio.sleep(0.001)
        
        # Force final flush
        await optimizer.force_flush()
        
        # Get final stats
        stats = optimizer.get_performance_stats()
        dashboard_metrics = optimizer.get_dashboard_metrics()
        
        print(f"\n=== Performance Test Results ===")
        print(f"Total events: {stats.total_events}")
        print(f"Total batches: {stats.total_batches}")
        print(f"Avg batch size: {stats.avg_batch_size:.1f}")
        print(f"Batching efficiency: {stats.batching_efficiency:.1%}")
        print(f"Throughput: {stats.throughput_eps:.1f} events/sec")
        print(f"Avg latency: {stats.avg_latency_ms:.1f}ms")
        print(f"P95 latency: {stats.p95_latency_ms:.1f}ms")
        print(f"Circuit trips: {stats.circuit_breaker_trips}")
        print(f"Error rate: {stats.error_rate:.1%}")
        print(f"Events dropped: {optimizer.events_dropped}")
        
        # Assertions
        assert stats.total_events >= 190  # Some might be dropped
        assert stats.batching_efficiency > 0.7  # Good batching
        assert stats.throughput_eps > 50  # Reasonable throughput
        assert dashboard_metrics["circuit_breaker"]["state"] in ["closed", "open", "half_open"]
        
        # Cleanup
        await optimizer.shutdown()
        
        print("✅ Performance optimization test passed")


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 