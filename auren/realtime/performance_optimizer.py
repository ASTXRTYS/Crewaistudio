"""
Performance Optimizer for AUREN Real-time Systems
Implements event batching, circuit breakers, and performance monitoring
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing recovery

@dataclass
class BatchMetrics:
    """Metrics for a single batch"""
    batch_id: str
    event_count: int
    batch_creation_time: datetime
    batch_send_time: datetime
    latency_ms: float
    success: bool
    size_bytes: int
    compression_ratio: float = 1.0

@dataclass
class PerformanceStats:
    """Aggregated performance statistics"""
    total_events: int
    total_batches: int
    avg_batch_size: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_eps: float  # Events per second
    batching_efficiency: float  # % of max batch size achieved
    circuit_breaker_trips: int
    error_rate: float
    last_updated: datetime

class EventBatcher:
    """
    Batches events for efficient transmission
    Collects up to max_batch_size events or max_wait_time_ms
    """
    
    def __init__(self,
                 max_batch_size: int = 50,
                 max_wait_time_ms: int = 100,
                 flush_callback: Optional[Callable] = None):
        self.max_batch_size = max_batch_size
        self.max_wait_time_ms = max_wait_time_ms
        self.flush_callback = flush_callback
        
        # Batch state
        self.current_batch: List[Any] = []
        self.batch_created_at: Optional[datetime] = None
        self.flush_task: Optional[asyncio.Task] = None
        self.batch_lock = asyncio.Lock()
        
        # Metrics
        self.batch_history = deque(maxlen=1000)
        self.total_events_batched = 0
        self.total_batches_sent = 0
    
    async def add_event(self, event: Any) -> None:
        """Add event to batch, triggering flush if needed"""
        
        async with self.batch_lock:
            # Start new batch if needed
            if not self.current_batch:
                self.batch_created_at = datetime.now(timezone.utc)
                # Schedule timeout flush
                self.flush_task = asyncio.create_task(self._timeout_flush())
            
            self.current_batch.append(event)
            self.total_events_batched += 1
            
            # Check if batch is full
            if len(self.current_batch) >= self.max_batch_size:
                await self._flush_batch("size_limit")
    
    async def _timeout_flush(self) -> None:
        """Flush batch after timeout"""
        await asyncio.sleep(self.max_wait_time_ms / 1000.0)
        async with self.batch_lock:
            if self.current_batch:
                await self._flush_batch("timeout")
    
    async def _flush_batch(self, reason: str) -> None:
        """Flush current batch"""
        
        if not self.current_batch:
            return
        
        # Cancel timeout task if running
        if self.flush_task and not self.flush_task.done():
            self.flush_task.cancel()
        
        # Prepare batch
        batch_to_send = self.current_batch.copy()
        batch_size = len(batch_to_send)
        batch_created = self.batch_created_at
        
        # Clear current batch
        self.current_batch = []
        self.batch_created_at = None
        self.total_batches_sent += 1
        
        # Calculate metrics
        send_time = datetime.now(timezone.utc)
        latency_ms = (send_time - batch_created).total_seconds() * 1000
        
        # Send batch via callback
        success = True
        if self.flush_callback:
            try:
                await self.flush_callback(batch_to_send, reason)
            except Exception as e:
                logger.error(f"Batch flush failed: {e}")
                success = False
        
        # Record metrics
        metrics = BatchMetrics(
            batch_id=f"batch_{self.total_batches_sent}",
            event_count=batch_size,
            batch_creation_time=batch_created,
            batch_send_time=send_time,
            latency_ms=latency_ms,
            success=success,
            size_bytes=self._estimate_batch_size(batch_to_send)
        )
        
        self.batch_history.append(metrics)
        logger.debug(f"Flushed batch: {batch_size} events, {latency_ms:.1f}ms latency, reason: {reason}")
    
    async def force_flush(self) -> None:
        """Force flush current batch"""
        async with self.batch_lock:
            if self.current_batch:
                await self._flush_batch("forced")
    
    def _estimate_batch_size(self, batch: List[Any]) -> int:
        """Estimate batch size in bytes"""
        # Simple estimation - in practice would serialize
        return len(str(batch))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get batching performance metrics"""
        
        if not self.batch_history:
            return {
                "total_events": 0,
                "total_batches": 0,
                "batching_efficiency": 0.0
            }
        
        recent_batches = list(self.batch_history)[-100:]  # Last 100 batches
        
        batch_sizes = [b.event_count for b in recent_batches]
        latencies = [b.latency_ms for b in recent_batches]
        successful = [b for b in recent_batches if b.success]
        
        return {
            "total_events": self.total_events_batched,
            "total_batches": self.total_batches_sent,
            "avg_batch_size": statistics.mean(batch_sizes) if batch_sizes else 0,
            "max_batch_size": max(batch_sizes) if batch_sizes else 0,
            "min_batch_size": min(batch_sizes) if batch_sizes else 0,
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
            "batching_efficiency": statistics.mean(batch_sizes) / self.max_batch_size if batch_sizes else 0,
            "success_rate": len(successful) / len(recent_batches) if recent_batches else 0,
            "current_batch_size": len(self.current_batch)
        }

class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    Protects against cascading failures
    """
    
    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout_seconds: int = 30,
                 half_open_max_calls: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout_seconds)
        self.half_open_max_calls = half_open_max_calls
        
        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0
        self.half_open_calls = 0
        self.state_changed_at = datetime.now(timezone.utc)
        
        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.trip_count = 0
        self.state_history = deque(maxlen=100)
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        
        self.total_calls += 1
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                await self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Retry after {self.recovery_timeout.total_seconds()}s"
                )
        
        # Attempt call
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
            
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self) -> None:
        """Handle successful call"""
        
        self.total_successes += 1
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                await self._transition_to_closed()
        
        elif self.state == CircuitState.OPEN:
            # Shouldn't happen, but reset if it does
            await self._transition_to_closed()
    
    async def _on_failure(self) -> None:
        """Handle failed call"""
        
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                await self._transition_to_open()
        
        elif self.state == CircuitState.HALF_OPEN:
            # Single failure in half-open trips the breaker
            await self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset from OPEN state"""
        
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.now(timezone.utc) - self.last_failure_time
        return time_since_failure >= self.recovery_timeout
    
    async def _transition_to_closed(self) -> None:
        """Transition to CLOSED state"""
        
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.state_changed_at = datetime.now(timezone.utc)
        
        self._record_state_change(old_state, self.state)
        logger.info("Circuit breaker transitioned to CLOSED")
    
    async def _transition_to_open(self) -> None:
        """Transition to OPEN state"""
        
        old_state = self.state
        self.state = CircuitState.OPEN
        self.state_changed_at = datetime.now(timezone.utc)
        self.trip_count += 1
        
        self._record_state_change(old_state, self.state)
        logger.warning(f"Circuit breaker TRIPPED to OPEN (trip #{self.trip_count})")
    
    async def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state"""
        
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.half_open_calls = 0
        self.state_changed_at = datetime.now(timezone.utc)
        
        self._record_state_change(old_state, self.state)
        logger.info("Circuit breaker transitioned to HALF_OPEN")
    
    def _record_state_change(self, from_state: CircuitState, to_state: CircuitState) -> None:
        """Record state transition"""
        
        self.state_history.append({
            "timestamp": datetime.now(timezone.utc),
            "from_state": from_state.value,
            "to_state": to_state.value,
            "failure_count": self.failure_count,
            "total_calls": self.total_calls
        })
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        
        uptime = datetime.now(timezone.utc) - self.state_changed_at
        
        return {
            "current_state": self.state.value,
            "failure_count": self.failure_count,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "failure_rate": self.total_failures / max(1, self.total_calls),
            "trip_count": self.trip_count,
            "state_duration_seconds": uptime.total_seconds(),
            "last_state_change": self.state_changed_at.isoformat()
        }

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass

class PerformanceOptimizer:
    """
    Main performance optimization orchestrator
    Combines batching and circuit breaking with monitoring
    """
    
    def __init__(self,
                 base_streamer,
                 batch_size: int = 50,
                 batch_timeout_ms: int = 100,
                 circuit_failure_threshold: int = 5,
                 circuit_recovery_seconds: int = 30):
        
        self.base_streamer = base_streamer
        
        # Initialize components
        self.batcher = EventBatcher(
            max_batch_size=batch_size,
            max_wait_time_ms=batch_timeout_ms,
            flush_callback=self._send_batch
        )
        
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_failure_threshold,
            recovery_timeout_seconds=circuit_recovery_seconds
        )
        
        # Performance tracking
        self.start_time = datetime.now(timezone.utc)
        self.events_processed = 0
        self.events_dropped = 0
        self.batch_send_times = deque(maxlen=1000)
        
        # Background tasks
        self.stats_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Initialize performance optimizer"""
        
        logger.info(f"Initializing PerformanceOptimizer - batch_size: {self.batcher.max_batch_size}, "
                   f"timeout: {self.batcher.max_wait_time_ms}ms")
        
        # Start background stats collection
        self.stats_task = asyncio.create_task(self._collect_stats())
    
    async def stream_event(self, event: Any) -> bool:
        """Stream event with optimization"""
        
        try:
            # Add to batch
            await self.batcher.add_event(event)
            self.events_processed += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to batch event: {e}")
            self.events_dropped += 1
            return False
    
    async def _send_batch(self, batch: List[Any], reason: str) -> None:
        """Send batch through circuit breaker"""
        
        start_time = time.time()
        
        try:
            # Send through circuit breaker
            await self.circuit_breaker.call(
                self._do_send_batch,
                batch
            )
            
            # Record timing
            send_time_ms = (time.time() - start_time) * 1000
            self.batch_send_times.append(send_time_ms)
            
            logger.debug(f"Batch sent successfully: {len(batch)} events in {send_time_ms:.1f}ms")
            
        except CircuitBreakerOpenError:
            # Circuit is open, drop batch
            self.events_dropped += len(batch)
            logger.warning(f"Dropped batch of {len(batch)} events - circuit breaker OPEN")
            raise
        
        except Exception as e:
            # Other errors
            self.events_dropped += len(batch)
            logger.error(f"Failed to send batch: {e}")
            raise
    
    async def _do_send_batch(self, batch: List[Any]) -> None:
        """Actually send the batch to base streamer"""
        
        # In production, might serialize/compress here
        
        # Send each event in batch
        # Could optimize by having batch endpoint
        for event in batch:
            success = await self.base_streamer.stream_event(event)
            if not success:
                raise Exception("Base streamer failed")
    
    async def force_flush(self) -> None:
        """Force flush any pending events"""
        await self.batcher.force_flush()
    
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        
        # Cancel stats task
        if self.stats_task:
            self.stats_task.cancel()
        
        # Flush remaining events
        await self.force_flush()
        
        logger.info("PerformanceOptimizer shutdown complete")
    
    async def _collect_stats(self) -> None:
        """Background task to collect performance statistics"""
        
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute
                
                stats = self.get_performance_stats()
                logger.info(f"Performance stats: {stats}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stats collection error: {e}")
    
    def calculate_throughput(self) -> float:
        """Calculate current throughput in events per second"""
        
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        if uptime <= 0:
            return 0.0
        
        return self.events_processed / uptime
    
    def get_performance_stats(self) -> PerformanceStats:
        """Get comprehensive performance statistics"""
        
        batch_metrics = self.batcher.get_metrics()
        circuit_metrics = self.circuit_breaker.get_metrics()
        
        # Calculate latencies
        recent_batches = list(self.batcher.batch_history)[-100:]
        if recent_batches:
            latencies = [b.latency_ms for b in recent_batches]
            avg_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
            p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
        else:
            avg_latency = p95_latency = p99_latency = 0.0
        
        return PerformanceStats(
            total_events=self.events_processed,
            total_batches=batch_metrics["total_batches"],
            avg_batch_size=batch_metrics["avg_batch_size"],
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            throughput_eps=self.calculate_throughput(),
            batching_efficiency=batch_metrics["batching_efficiency"],
            circuit_breaker_trips=circuit_metrics["trip_count"],
            error_rate=circuit_metrics["failure_rate"],
            last_updated=datetime.now(timezone.utc)
        )
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get metrics formatted for dashboard display"""
        
        stats = self.get_performance_stats()
        batch_metrics = self.batcher.get_metrics()
        circuit_metrics = self.circuit_breaker.get_metrics()
        
        return {
            "performance_stats": asdict(stats),
            "batching": {
                "current_batch_size": batch_metrics["current_batch_size"],
                "efficiency": batch_metrics["batching_efficiency"] * 100,  # As percentage
                "avg_batch_size": batch_metrics["avg_batch_size"],
                "total_batches": batch_metrics["total_batches"]
            },
            "circuit_breaker": {
                "state": circuit_metrics["current_state"],
                "failure_rate": circuit_metrics["failure_rate"] * 100,  # As percentage
                "trip_count": circuit_metrics["trip_count"],
                "uptime_seconds": circuit_metrics["state_duration_seconds"]
            },
            "throughput": {
                "events_per_second": stats.throughput_eps,
                "events_dropped": self.events_dropped,
                "drop_rate": (self.events_dropped / max(1, self.events_processed)) * 100
            },
            "latency": {
                "avg_ms": stats.avg_latency_ms,
                "p95_ms": stats.p95_latency_ms,
                "p99_ms": stats.p99_latency_ms
            }
        }

class LoadTestGenerator:
    """Generate load for testing performance optimizer"""
    
    def __init__(self, target_eps: float = 1000):
        self.target_eps = target_eps
        self.events_generated = 0
        self.running = False
    
    async def generate_load(self, optimizer: PerformanceOptimizer, duration_seconds: int = 60):
        """Generate load for specified duration"""
        
        self.running = True
        start_time = time.time()
        event_interval = 1.0 / self.target_eps
        
        logger.info(f"Starting load test: {self.target_eps} events/sec for {duration_seconds}s")
        
        while self.running and (time.time() - start_time) < duration_seconds:
            # Generate event
            event = self._create_test_event()
            
            # Stream through optimizer
            await optimizer.stream_event(event)
            self.events_generated += 1
            
            # Wait for next event
            await asyncio.sleep(event_interval)
        
        self.running = False
        logger.info(f"Load test complete: {self.events_generated} events generated")
    
    def _create_test_event(self) -> Dict[str, Any]:
        """Create test event"""
        
        from auren.realtime.langgraph_instrumentation import AURENStreamEvent, AURENEventType
        import uuid
        
        return AURENStreamEvent(
            event_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            session_id="load_test",
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.PERFORMANCE_METRIC,
            source_agent={"id": "load_tester"},
            target_agent=None,
            payload={
                "test_event": True,
                "sequence": self.events_generated,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            metadata={
                "load_test": True,
                "target_eps": self.target_eps
            }
        )
    
    def stop(self):
        """Stop load generation"""
        self.running = False 