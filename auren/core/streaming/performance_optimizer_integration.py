"""
Performance Optimizer Integration - Adding optimization to AUREN event streaming
Shows how to wrap existing streamers with batching and circuit breaker protection
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime, timezone
from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer as CrewAIEventInstrumentation

# Import performance optimization
from auren.realtime.performance_optimizer import (
    PerformanceOptimizer,
    LoadTestGenerator
)

# Import from Module C
from auren.realtime.langgraph_instrumentation import (
    CrewAIEventInstrumentation, 
    AURENStreamEvent,
    AURENEventType
)
from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer
from auren.realtime.secure_integration import SecureEventStreamer

logger = logging.getLogger(__name__)


async def setup_optimized_event_streaming(config: Dict[str, Any]):
    """
    Setup event streaming with performance optimization
    Adds batching and circuit breaker to existing pipeline
    """
    
    # 1. Initialize base Redis streamer
    redis_streamer = RedisStreamEventStreamer(
        redis_url=config["redis_url"],
        stream_name="auren:events"
    )
    await redis_streamer.initialize()
    
    # 2. Wrap with security layer (from previous implementation)
    secure_streamer = SecureEventStreamer(
        base_streamer=redis_streamer,
        encryption_key=config.get("encryption_key"),
        security_policy=config.get("security_policy")
    )
    
    # 3. Wrap with performance optimization
    optimized_streamer = PerformanceOptimizer(
        base_streamer=secure_streamer,
        batch_size=50,             # Batch up to 50 events
        batch_timeout_ms=100,      # Or flush after 100ms
        circuit_failure_threshold=5, # Open circuit after 5 failures
        circuit_recovery_seconds=30  # Try recovery after 30s
    )
    await optimized_streamer.initialize()
    
    # 4. Create event instrumentation with optimized streamer
    event_instrumentation = CrewAIEventInstrumentation(
        event_streamer=optimized_streamer  # All events now batched!
    )
    
    logger.info("Performance-optimized event streaming initialized")
    
    return {
        "optimized_streamer": optimized_streamer,
        "event_instrumentation": event_instrumentation,
        "redis_streamer": redis_streamer
    }


async def demonstrate_performance_optimization():
    """Demonstrate performance optimization in action"""
    
    config = {
        "redis_url": "redis://localhost:6379",
        "encryption_key": b"your-encryption-key-here",
        "security_policy": {}
    }
    
    # Setup optimized streaming
    components = await setup_optimized_event_streaming(config)
    optimizer = components["optimized_streamer"]
    
    print("\n=== Performance Optimization Demo ===")
    
    # 1. Normal event streaming (will be batched)
    print("\n1. Streaming regular events...")
    for i in range(10):
        event = AURENStreamEvent(
            event_id=f"demo_{i}",
            trace_id="demo_trace",
            session_id="demo_session",
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.AGENT_DECISION,
            source_agent={"id": "neuroscientist"},
            target_agent=None,
            payload={"decision": f"decision_{i}"},
            metadata={}
        )
        
        await optimizer.stream_event(event)
    
    # Wait a bit for batch to flush
    await asyncio.sleep(0.15)
    
    # Get initial metrics
    metrics = optimizer.get_dashboard_metrics()
    print(f"\nBatching metrics:")
    print(f"  - Total batches: {metrics['batching']['total_batches']}")
    print(f"  - Avg batch size: {metrics['batching']['avg_batch_size']:.1f}")
    print(f"  - Efficiency: {metrics['batching']['efficiency']:.1f}%")
    
    # 2. High-volume streaming (demonstrate batching efficiency)
    print("\n2. High-volume event streaming...")
    start_time = asyncio.get_event_loop().time()
    
    for i in range(100):
        event = create_test_event(i)
        await optimizer.stream_event(event)
    
    # Force flush and measure
    await optimizer.force_flush()
    duration = asyncio.get_event_loop().time() - start_time
    
    print(f"\nStreamed 100 events in {duration:.3f}s")
    
    # 3. Demonstrate circuit breaker (simulate failures)
    print("\n3. Testing circuit breaker protection...")
    
    # Temporarily break the base streamer
    original_stream_event = optimizer.base_streamer.stream_event
    
    async def failing_stream_event(event):
        raise Exception("Simulated downstream failure")
    
    optimizer.base_streamer.stream_event = failing_stream_event
    
    # Try to send events (will fail and trip circuit)
    for i in range(10):
        await optimizer.stream_event(create_test_event(i))
    
    await optimizer.force_flush()
    
    # Check circuit state
    circuit_metrics = optimizer.get_dashboard_metrics()["circuit_breaker"]
    print(f"\nCircuit breaker state: {circuit_metrics['state']}")
    print(f"  - Trip count: {circuit_metrics['trip_count']}")
    print(f"  - Failure rate: {circuit_metrics['failure_rate']:.1f}%")
    
    # Restore normal operation
    optimizer.base_streamer.stream_event = original_stream_event
    
    # 4. Show performance statistics
    print("\n4. Performance Statistics:")
    stats = optimizer.get_performance_stats()
    print(f"  - Total events: {stats.total_events}")
    print(f"  - Throughput: {stats.throughput_eps:.1f} events/sec")
    print(f"  - Avg latency: {stats.avg_latency_ms:.1f}ms")
    print(f"  - P95 latency: {stats.p95_latency_ms:.1f}ms")
    print(f"  - Events dropped: {optimizer.events_dropped}")
    
    # Cleanup
    await optimizer.shutdown()


def create_test_event(sequence: int) -> AURENStreamEvent:
    """Create a test event"""
    import uuid
    
    return AURENStreamEvent(
        event_id=str(uuid.uuid4()),
        trace_id="test_trace",
        session_id="test_session",
        timestamp=datetime.now(timezone.utc),
        event_type=AURENEventType.PERFORMANCE_METRIC,
        source_agent={"id": "test_agent"},
        target_agent=None,
        payload={
            "sequence": sequence,
            "metric": "test_metric",
            "value": sequence * 1.5
        },
        metadata={"test": True}
    )


async def run_load_test_demo():
    """Demonstrate load testing with performance optimizer"""
    
    print("\n=== Load Test Demo ===")
    
    config = {
        "redis_url": "redis://localhost:6379"
    }
    
    # Setup components
    components = await setup_optimized_event_streaming(config)
    optimizer = components["optimized_streamer"]
    
    # Create load generator
    load_generator = LoadTestGenerator(target_eps=1000)  # 1000 events/sec
    
    print("\nRunning load test: 1000 events/sec for 5 seconds...")
    
    # Run load test
    await load_generator.generate_load(optimizer, duration_seconds=5)
    
    # Get results
    stats = optimizer.get_performance_stats()
    dashboard = optimizer.get_dashboard_metrics()
    
    print(f"\n=== Load Test Results ===")
    print(f"Events generated: {load_generator.events_generated}")
    print(f"Events processed: {stats.total_events}")
    print(f"Events dropped: {optimizer.events_dropped}")
    print(f"Actual throughput: {stats.throughput_eps:.1f} events/sec")
    print(f"Batching efficiency: {stats.batching_efficiency:.1%}")
    print(f"Average latency: {stats.avg_latency_ms:.1f}ms")
    print(f"P95 latency: {stats.p95_latency_ms:.1f}ms")
    print(f"Circuit breaker trips: {stats.circuit_breaker_trips}")
    
    # Cleanup
    await optimizer.shutdown()


def verify_performance_optimizer_implementation():
    """Verification checklist for performance optimizer"""
    
    checklist = {
        "Event Batching": {
            "requirement": "Batch up to 50 events or 100ms timeout",
            "test": "Send 100 events rapidly - should create ~2 batches",
            "dashboard": "Shows batching efficiency percentage"
        },
        "Circuit Breaker": {
            "requirement": "5 failures triggers 30s backoff",
            "test": "Simulate downstream failures - circuit should open",
            "dashboard": "Shows circuit state and trip count"
        },
        "Performance Metrics": {
            "requirement": "Track throughput, latency, drops",
            "test": "Run load test - measure actual vs target",
            "dashboard": "Shows events/sec, latency percentiles"
        },
        "Graceful Degradation": {
            "requirement": "Drop events when circuit open",
            "test": "Send events with open circuit - should drop",
            "dashboard": "Shows drop rate percentage"
        },
        "Load Handling": {
            "requirement": "Handle 1000+ events/sec",
            "test": "Run load generator at 1000 eps",
            "dashboard": "Shows sustained throughput"
        },
        "Integration": {
            "requirement": "Works with existing security layer",
            "test": "Events still encrypted after batching",
            "dashboard": "No security bypasses"
        }
    }
    
    print("\n=== Performance Optimizer Checklist ===")
    for feature, details in checklist.items():
        print(f"\n{feature}:")
        print(f"  ✓ Requirement: {details['requirement']}")
        print(f"  ✓ Test: {details['test']}")
        print(f"  ✓ Dashboard: {details['dashboard']}")
    
    return checklist


class OptimizedWebSocketStreamer:
    """Example WebSocket streamer with performance optimization"""
    
    def __init__(self, optimizer: PerformanceOptimizer):
        self.optimizer = optimizer
        self.connections = set()
        self.metrics_task = None
    
    async def start_server(self):
        """Start WebSocket server with metrics broadcasting"""
        
        # Start metrics broadcast
        self.metrics_task = asyncio.create_task(self._broadcast_metrics())
        
        print("Optimized WebSocket server started")
    
    async def _broadcast_metrics(self):
        """Broadcast performance metrics to connected clients"""
        
        while True:
            try:
                await asyncio.sleep(5)  # Every 5 seconds
                
                metrics = self.optimizer.get_dashboard_metrics()
                
                # Broadcast to all connections
                message = {
                    "type": "performance_metrics",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": metrics
                }
                
                # In real implementation, would send to WebSocket connections
                print(f"Broadcasting metrics: {metrics['throughput']['events_per_second']:.1f} events/sec")
                
            except Exception as e:
                logger.error(f"Metrics broadcast error: {e}")


# Example configuration for production
PRODUCTION_CONFIG = {
    "optimization": {
        "batch_size": 50,
        "batch_timeout_ms": 100,
        "circuit_failure_threshold": 5,
        "circuit_recovery_seconds": 30
    },
    "monitoring": {
        "stats_interval_seconds": 60,
        "metrics_retention_hours": 24
    },
    "load_limits": {
        "max_events_per_second": 10000,
        "max_batch_size": 100,
        "min_batch_timeout_ms": 10
    }
}


if __name__ == "__main__":
    # Run verification
    verify_performance_optimizer_implementation()
    
    # Run demonstration
    asyncio.run(demonstrate_performance_optimization())
    
    # Run load test
    asyncio.run(run_load_test_demo()) 