# =============================================================================
# AUREN PROMETHEUS METRICS IMPLEMENTATION
# =============================================================================
# Complete instrumentation for the biometric API with memory tier tracking
# Created by: Senior Engineer
# Date: January 2025
# =============================================================================

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI, Response
from typing import Callable
import time
import psutil
import hashlib
import json
from datetime import datetime

# =============================================================================
# CORE METRICS DEFINITIONS
# =============================================================================

# Four Golden Signals
webhook_requests_total = Counter(
    'auren_webhook_requests_total',
    'Total number of webhook requests received',
    ['device_type', 'event_type', 'status']
)

webhook_request_duration_seconds = Histogram(
    'auren_webhook_request_duration_seconds',
    'Webhook request duration in seconds',
    ['device_type', 'method'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

webhook_errors_total = Counter(
    'auren_webhook_errors_total',
    'Total number of webhook processing errors',
    ['device_type', 'error_type']
)

webhook_active_requests = Gauge(
    'auren_webhook_active_requests',
    'Number of webhook requests currently being processed',
    ['device_type']
)

# =============================================================================
# MEMORY TIER METRICS (For the Founder's Visualization!)
# =============================================================================

memory_tier_operations_total = Counter(
    'auren_memory_tier_operations_total',
    'Total memory tier operations by the AI agent',
    ['tier', 'operation', 'trigger']
)

memory_tier_size_bytes = Gauge(
    'auren_memory_tier_size_bytes',
    'Current size of each memory tier in bytes',
    ['tier']
)

memory_tier_latency_seconds = Histogram(
    'auren_memory_tier_latency_seconds',
    'Latency of memory tier operations',
    ['tier', 'operation'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
)

ai_agent_decisions_total = Counter(
    'auren_ai_agent_decisions_total',
    'Total decisions made by NEUROS AI agent',
    ['decision_type', 'from_tier', 'to_tier']
)

# =============================================================================
# BIOMETRIC EVENT METRICS
# =============================================================================

biometric_events_processed_total = Counter(
    'auren_biometric_events_processed_total',
    'Total biometric events processed',
    ['device_type', 'event_type', 'user_id_hash']
)

biometric_event_values = Histogram(
    'auren_biometric_event_values',
    'Distribution of biometric values',
    ['device_type', 'metric_type'],
    buckets=(20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200)
)

# =============================================================================
# NEUROS MODE METRICS
# =============================================================================

neuros_mode_switches_total = Counter(
    'auren_neuros_mode_switches_total',
    'Total NEUROS cognitive mode switches',
    ['from_mode', 'to_mode', 'trigger_type']
)

neuros_current_mode = Gauge(
    'auren_neuros_current_mode',
    'Current NEUROS mode per user (1=baseline, 2=reflex, 3=hypothesis, 4=pattern, 5=companion)',
    ['user_id_hash']
)

# =============================================================================
# SYSTEM HEALTH METRICS
# =============================================================================

system_info = Info(
    'auren_system',
    'AUREN system information'
)

kafka_messages_sent_total = Counter(
    'auren_kafka_messages_sent_total',
    'Total messages sent to Kafka',
    ['topic']
)

kafka_message_send_errors_total = Counter(
    'auren_kafka_message_send_errors_total',
    'Total Kafka message send errors',
    ['topic', 'error_type']
)

# System resource gauges
system_cpu_usage = Gauge('auren_system_cpu_usage_percent', 'System CPU usage')
system_memory_usage = Gauge('auren_system_memory_usage_percent', 'System memory usage')

# =============================================================================
# ENHANCED FASTAPI INSTRUMENTATOR
# =============================================================================

def create_instrumentator() -> Instrumentator:
    """Create and configure the Prometheus instrumentator for FastAPI"""
    
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health", "/ready"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="auren_http_requests_inprogress",
        inprogress_labels=True,
    )
    
    # Add custom metrics
    @instrumentator.add
    def memory_tier_info(info):
        """Track memory tier operations from request context"""
        if hasattr(info.request.state, "memory_operation"):
            op = info.request.state.memory_operation
            memory_tier_operations_total.labels(
                tier=op.get("tier", "unknown"),
                operation=op.get("operation", "unknown"),
                trigger=op.get("trigger", "manual")
            ).inc()
    
    @instrumentator.add
    def system_metrics(info):
        """Collect system-level metrics"""
        # CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Update system gauges
        system_cpu_usage.set(cpu_percent)
        system_memory_usage.set(memory.percent)
    
    return instrumentator

# =============================================================================
# METRICS ENDPOINT IMPLEMENTATION
# =============================================================================

def setup_metrics_endpoint(app: FastAPI):
    """Setup the /metrics endpoint for Prometheus scraping"""
    
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        """Expose metrics in Prometheus format"""
        # Update system info
        system_info.info({
            'version': '1.0.0',
            'environment': 'production',
            'deployment': 'docker'
        })
        
        # Generate and return metrics
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )

# =============================================================================
# HELPER FUNCTIONS FOR METRIC TRACKING
# =============================================================================

def track_memory_promotion(user_id: str, from_tier: str, to_tier: str, size_bytes: int, reason: str):
    """Track when AI agent promotes data between memory tiers"""
    # Hash user_id for privacy
    user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    
    # Record the operation
    memory_tier_operations_total.labels(
        tier=to_tier,
        operation="promote",
        trigger=reason
    ).inc()
    
    # Record AI decision
    ai_agent_decisions_total.labels(
        decision_type="tier_promotion",
        from_tier=from_tier,
        to_tier=to_tier
    ).inc()
    
    # Update tier sizes
    memory_tier_size_bytes.labels(tier=to_tier).inc(size_bytes)
    if from_tier != "none":
        memory_tier_size_bytes.labels(tier=from_tier).dec(size_bytes)

def track_webhook_metrics(device_type: str, event_type: str, duration: float, status: str, error: str = None):
    """Track webhook processing metrics"""
    webhook_requests_total.labels(
        device_type=device_type,
        event_type=event_type,
        status=status
    ).inc()
    
    webhook_request_duration_seconds.labels(
        device_type=device_type,
        method="POST"
    ).observe(duration)
    
    if error:
        webhook_errors_total.labels(
            device_type=device_type,
            error_type=error
        ).inc()

def track_biometric_event(device_type: str, event_type: str, user_id: str, metrics: dict):
    """Track biometric event processing"""
    user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    
    biometric_events_processed_total.labels(
        device_type=device_type,
        event_type=event_type,
        user_id_hash=user_hash
    ).inc()
    
    # Track specific metric values
    for metric_name, value in metrics.items():
        if isinstance(value, (int, float)):
            biometric_event_values.labels(
                device_type=device_type,
                metric_type=metric_name
            ).observe(value)

def track_neuros_mode_switch(user_id: str, from_mode: str, to_mode: str, trigger: str):
    """Track NEUROS cognitive mode switches"""
    user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    
    neuros_mode_switches_total.labels(
        from_mode=from_mode,
        to_mode=to_mode,
        trigger_type=trigger
    ).inc()
    
    # Update current mode gauge
    mode_values = {
        "baseline": 1,
        "reflex": 2,
        "hypothesis": 3,
        "pattern": 4,
        "companion": 5
    }
    
    neuros_current_mode.labels(user_id_hash=user_hash).set(
        mode_values.get(to_mode, 0)
    )

def track_kafka_message(topic: str, success: bool, error_type: str = None):
    """Track Kafka message operations"""
    kafka_messages_sent_total.labels(topic=topic).inc()
    
    if not success and error_type:
        kafka_message_send_errors_total.labels(
            topic=topic,
            error_type=error_type
        ).inc()

# =============================================================================
# INSTRUMENTED BIOMETRIC PROCESSOR
# =============================================================================

class InstrumentedBiometricProcessor:
    """Enhanced processor with memory tier tracking"""
    
    def __init__(self, base_processor):
        self.processor = base_processor
        self.redis = base_processor.redis
        self.chroma_client = getattr(base_processor, 'chroma_client', None)
    
    async def promote_to_hot_tier(self, user_id: str, data: dict, size_bytes: int = None):
        """Promote data to Redis hot tier with metrics"""
        start_time = time.time()
        
        try:
            # Calculate size if not provided
            if size_bytes is None:
                size_bytes = len(json.dumps(data).encode('utf-8'))
            
            # Existing Redis operation
            await self.redis.setex(
                f"biometric:hot:{user_id}:latest",
                300,  # 5 minute TTL
                json.dumps(data)
            )
            
            # Track the operation
            track_memory_promotion(
                user_id=user_id,
                from_tier="warm",
                to_tier="hot",
                size_bytes=size_bytes,
                reason="frequency_threshold"
            )
            
            # Track latency
            latency = time.time() - start_time
            memory_tier_latency_seconds.labels(
                tier="hot",
                operation="promote"
            ).observe(latency)
            
        except Exception as e:
            print(f"Failed to promote to hot tier: {e}")
            raise
    
    async def archive_to_cold_tier(self, user_id: str, data: dict, size_bytes: int = None):
        """Archive to ChromaDB cold tier with metrics"""
        start_time = time.time()
        
        try:
            if self.chroma_client:
                # Calculate size if not provided
                if size_bytes is None:
                    size_bytes = len(json.dumps(data).encode('utf-8'))
                
                # ChromaDB operation
                collection = self.chroma_client.get_or_create_collection("biometric_patterns")
                collection.add(
                    documents=[json.dumps(data)],
                    metadatas=[{"user_id": user_id, "archived_at": datetime.utcnow().isoformat()}],
                    ids=[f"{user_id}_{datetime.utcnow().timestamp()}"]
                )
                
                # Track the operation
                track_memory_promotion(
                    user_id=user_id,
                    from_tier="warm",
                    to_tier="cold",
                    size_bytes=size_bytes,
                    reason="age_threshold"
                )
                
                # Track latency
                latency = time.time() - start_time
                memory_tier_latency_seconds.labels(
                    tier="cold",
                    operation="archive"
                ).observe(latency)
            
        except Exception as e:
            print(f"Failed to archive to cold tier: {e}")
            raise
    
    # Delegate all other methods to the base processor
    def __getattr__(self, name):
        return getattr(self.processor, name) 