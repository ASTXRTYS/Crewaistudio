# AUREN INTEGRATION PATTERNS

**Created**: January 28, 2025  
**Author**: Senior Engineer  
**Version**: 1.0  
**Purpose**: Best practices for integrating new features with AUREN

---

## 🎯 Overview

This guide provides patterns and best practices for integrating new features into AUREN, with a focus on observability, performance, and maintainability.

---

## 📊 Metrics Integration Pattern

### Adding Metrics to New Endpoints

```python
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Define metrics at module level
endpoint_requests_total = Counter(
    'auren_endpoint_requests_total',
    'Total requests to custom endpoints',
    ['endpoint', 'method', 'status']
)

endpoint_duration_seconds = Histogram(
    'auren_endpoint_duration_seconds',
    'Request duration for custom endpoints',
    ['endpoint', 'method']
)

# Decorator pattern for automatic metrics
def track_metrics(endpoint_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                endpoint_requests_total.labels(
                    endpoint=endpoint_name,
                    method="POST",
                    status=status
                ).inc()
                endpoint_duration_seconds.labels(
                    endpoint=endpoint_name,
                    method="POST"
                ).observe(duration)
        
        return wrapper
    return decorator

# Usage example
@app.post("/api/v1/custom-endpoint")
@track_metrics("custom_endpoint")
async def custom_endpoint(request: Request):
    # Your endpoint logic here
    pass
```

### Context Manager Pattern for Operations

```python
from contextlib import asynccontextmanager
from typing import Optional

class OperationMetrics:
    """Context manager for tracking operation metrics"""
    
    def __init__(self, operation_type: str, tier: str):
        self.operation_type = operation_type
        self.tier = tier
        self.start_time = None
        self.success = True
        
    async def __aenter__(self):
        self.start_time = time.time()
        # Increment active operations gauge
        active_operations.labels(
            operation=self.operation_type,
            tier=self.tier
        ).inc()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.success = exc_type is None
        
        # Track operation
        operations_total.labels(
            operation=self.operation_type,
            tier=self.tier,
            success=str(self.success)
        ).inc()
        
        operation_duration.labels(
            operation=self.operation_type,
            tier=self.tier
        ).observe(duration)
        
        # Decrement active operations
        active_operations.labels(
            operation=self.operation_type,
            tier=self.tier
        ).dec()
        
        return False  # Don't suppress exceptions

# Usage
async def process_data(user_id: str, data: dict):
    async with OperationMetrics("process", "warm") as metrics:
        # Your processing logic
        result = await database.store(user_id, data)
        return result
```

---

## 🧠 Memory Tier Integration Pattern

### Adding Memory Tier Support to New Features

```python
from typing import Optional, Dict, Any
import json
import hashlib
from datetime import datetime, timedelta

class TieredDataManager:
    """Pattern for managing data across memory tiers"""
    
    def __init__(self, redis_client, postgres_pool, chroma_client):
        self.redis = redis_client
        self.postgres = postgres_pool
        self.chroma = chroma_client
        
    async def get_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data with tier fallback"""
        # Check hot tier first
        hot_data = await self._get_from_hot(key)
        if hot_data:
            memory_tier_hit_rate.labels(tier="hot").set(1.0)
            return hot_data
            
        # Check warm tier
        warm_data = await self._get_from_warm(key)
        if warm_data:
            memory_tier_hit_rate.labels(tier="hot").set(0.0)
            # Promote to hot tier if frequently accessed
            await self._maybe_promote_to_hot(key, warm_data)
            return warm_data
            
        # Check cold tier
        cold_data = await self._get_from_cold(key)
        if cold_data:
            # Promote through tiers if needed
            await self._promote_from_cold(key, cold_data)
            return cold_data
            
        return None
        
    async def store_data(self, key: str, data: Dict[str, Any], 
                        tier: str = "warm") -> None:
        """Store data in appropriate tier"""
        async with OperationMetrics("store", tier):
            if tier == "hot":
                await self._store_in_hot(key, data)
            elif tier == "warm":
                await self._store_in_warm(key, data)
            elif tier == "cold":
                await self._store_in_cold(key, data)
                
            # Track storage
            size_bytes = len(json.dumps(data).encode('utf-8'))
            memory_tier_size_bytes.labels(tier=tier).inc(size_bytes)
            
    async def _maybe_promote_to_hot(self, key: str, data: Dict[str, Any]):
        """Promote data to hot tier based on access patterns"""
        access_count = await self._get_access_count(key)
        if access_count > 5:  # Threshold for promotion
            await self._store_in_hot(key, data)
            
            # Track promotion
            ai_agent_decisions_total.labels(
                decision_type="tier_promotion",
                from_tier="warm",
                to_tier="hot",
                reason="frequency_threshold"
            ).inc()
```

### Memory Pressure Management Pattern

```python
class MemoryPressureManager:
    """Handle memory pressure and tier management"""
    
    def __init__(self, hot_tier_limit_bytes: int = 256 * 1024 * 1024):
        self.hot_tier_limit = hot_tier_limit_bytes
        
    async def check_memory_pressure(self) -> float:
        """Check current memory pressure (0.0 to 1.0)"""
        current_size = await self._get_hot_tier_size()
        pressure = current_size / self.hot_tier_limit
        
        # Update gauge
        memory_pressure_ratio.set(pressure)
        
        if pressure > 0.8:
            await self._evict_cold_data()
            
        return pressure
        
    async def _evict_cold_data(self):
        """Evict least recently used data from hot tier"""
        # Get LRU candidates
        candidates = await self._get_lru_candidates(limit=10)
        
        for key, data in candidates:
            # Move to warm tier
            await self._demote_to_warm(key, data)
            
            # Track demotion
            ai_agent_decisions_total.labels(
                decision_type="tier_demotion",
                from_tier="hot",
                to_tier="warm",
                reason="memory_pressure"
            ).inc()
```

---

## 🎨 NEUROS Mode Integration Pattern

### Adding Mode-Aware Behavior

```python
from enum import Enum
from typing import Optional

class NEUROSMode(Enum):
    BASELINE = "baseline"
    REFLEX = "reflex"
    HYPOTHESIS = "hypothesis"
    PATTERN = "pattern"
    COMPANION = "companion"
    SENTINEL = "sentinel"

class ModeAwareProcessor:
    """Pattern for NEUROS mode-aware processing"""
    
    def __init__(self):
        self.current_modes: Dict[str, NEUROSMode] = {}
        
    async def process_with_mode(self, user_id: str, data: Dict[str, Any]):
        """Process data according to current NEUROS mode"""
        mode = await self._get_current_mode(user_id)
        
        if mode == NEUROSMode.REFLEX:
            # Fast, reactive processing
            result = await self._reflex_process(data)
        elif mode == NEUROSMode.HYPOTHESIS:
            # Generate and test hypotheses
            result = await self._hypothesis_process(data)
        elif mode == NEUROSMode.PATTERN:
            # Look for patterns
            result = await self._pattern_process(data)
        else:
            # Default baseline processing
            result = await self._baseline_process(data)
            
        return result
        
    async def switch_mode(self, user_id: str, new_mode: NEUROSMode, 
                         trigger: str = "manual"):
        """Switch NEUROS mode with tracking"""
        old_mode = self.current_modes.get(user_id, NEUROSMode.BASELINE)
        
        # Track the switch
        neuros_mode_switches_total.labels(
            from_mode=old_mode.value,
            to_mode=new_mode.value,
            trigger_type=trigger,
            user_id_hash=hashlib.sha256(user_id.encode()).hexdigest()[:8]
        ).inc()
        
        # Update current mode
        self.current_modes[user_id] = new_mode
        neuros_current_mode.labels(
            user_id_hash=hashlib.sha256(user_id.encode()).hexdigest()[:8]
        ).state(new_mode.value)
        
    async def _reflex_process(self, data: Dict[str, Any]):
        """Quick reactive processing for immediate responses"""
        # Implement reflex logic
        pass
        
    async def _hypothesis_process(self, data: Dict[str, Any]):
        """Generate and track hypotheses"""
        hypothesis = self._generate_hypothesis(data)
        
        # Track hypothesis
        neuros_hypothesis_generated_total.labels(
            category=hypothesis["category"],
            confidence_level=hypothesis["confidence"]
        ).inc()
        
        return hypothesis
```

---

## 🔌 Webhook Integration Pattern

### Adding New Device Integrations

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class DeviceWebhookBase(BaseModel):
    """Base pattern for device webhooks"""
    user_id: str
    timestamp: datetime
    device_type: str
    event_type: str
    data: Dict[str, Any]

class WebhookProcessor:
    """Pattern for processing device webhooks"""
    
    def __init__(self, biometric_processor):
        self.processor = biometric_processor
        self.device_handlers = {
            "oura": self._process_oura,
            "whoop": self._process_whoop,
            "healthkit": self._process_healthkit,
            # Add new devices here
        }
        
    async def process_webhook(self, device_type: str, payload: dict):
        """Process webhook with full observability"""
        async with WebhookMetrics(device_type) as metrics:
            # Validate payload
            try:
                webhook_data = DeviceWebhookBase(
                    device_type=device_type,
                    **payload
                )
                metrics.event_type = webhook_data.event_type
                metrics.payload_size = len(json.dumps(payload).encode())
            except ValidationError as e:
                webhook_errors_total.labels(
                    device_type=device_type,
                    error_type="validation_error"
                ).inc()
                raise
                
            # Get device-specific handler
            handler = self.device_handlers.get(device_type)
            if not handler:
                raise ValueError(f"Unknown device type: {device_type}")
                
            # Process with handler
            result = await handler(webhook_data)
            
            # Track biometric event
            await self._track_biometric_event(webhook_data, result)
            
            return result
            
    async def _track_biometric_event(self, webhook: DeviceWebhookBase, 
                                    result: Dict[str, Any]):
        """Track biometric event metrics"""
        user_hash = hashlib.sha256(webhook.user_id.encode()).hexdigest()[:8]
        
        biometric_events_processed_total.labels(
            device_type=webhook.device_type,
            event_type=webhook.event_type,
            user_id_hash=user_hash
        ).inc()
        
        # Track specific metrics
        for metric_name, value in result.get("metrics", {}).items():
            if isinstance(value, (int, float)):
                biometric_event_values.labels(
                    device_type=webhook.device_type,
                    metric_type=metric_name,
                    unit=self._infer_unit(metric_name)
                ).observe(value)
```

### Adding Data Quality Checks

```python
class DataQualityChecker:
    """Pattern for checking biometric data quality"""
    
    def __init__(self):
        self.quality_rules = {
            "heart_rate": (30, 250),  # min, max
            "hrv": (10, 200),
            "temperature": (35.0, 42.0),
            "spo2": (70, 100),
        }
        
    async def check_quality(self, device_type: str, metrics: Dict[str, Any]) -> float:
        """Check data quality and track anomalies"""
        quality_score = 1.0
        anomalies = []
        
        for metric_name, value in metrics.items():
            if metric_name in self.quality_rules:
                min_val, max_val = self.quality_rules[metric_name]
                
                if not min_val <= value <= max_val:
                    anomalies.append({
                        "metric": metric_name,
                        "value": value,
                        "type": "out_of_range"
                    })
                    quality_score *= 0.8
                    
        # Track anomalies
        for anomaly in anomalies:
            biometric_anomalies_detected_total.labels(
                device_type=device_type,
                anomaly_type=anomaly["type"],
                severity="medium" if quality_score > 0.5 else "high"
            ).inc()
            
        # Update quality score
        biometric_data_quality_score.labels(
            device_type=device_type,
            user_id_hash="aggregate"
        ).set(quality_score)
        
        return quality_score
```

---

## 🚀 Kafka Integration Pattern

### Adding Event Streaming

```python
from aiokafka import AIOKafkaProducer
import json
import asyncio

class EventStreamPublisher:
    """Pattern for publishing events to Kafka"""
    
    def __init__(self, kafka_config: dict):
        self.producer = None
        self.config = kafka_config
        
    async def start(self):
        """Initialize Kafka producer"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.config["bootstrap_servers"],
            value_serializer=lambda v: json.dumps(v).encode()
        )
        await self.producer.start()
        
    async def publish_event(self, topic: str, event: dict, key: str = None):
        """Publish event with metrics tracking"""
        start_time = time.time()
        
        try:
            # Send to Kafka
            await self.producer.send_and_wait(
                topic=topic,
                value=event,
                key=key.encode() if key else None
            )
            
            # Track success
            kafka_messages_sent_total.labels(
                topic=topic,
                status="success"
            ).inc()
            
        except Exception as e:
            # Track failure
            kafka_messages_sent_total.labels(
                topic=topic,
                status="failed"
            ).inc()
            raise
            
        finally:
            # Track duration
            duration = time.time() - start_time
            kafka_message_send_duration_seconds.labels(
                topic=topic
            ).observe(duration)
            
    async def publish_batch(self, topic: str, events: List[dict]):
        """Publish batch of events"""
        batch_size = len(events)
        
        # Track batch size
        kafka_batch_size.labels(topic=topic).observe(batch_size)
        
        # Send all events
        futures = []
        for event in events:
            future = await self.producer.send(topic, event)
            futures.append(future)
            
        # Wait for all to complete
        await asyncio.gather(*[f for f in futures])
```

---

## 📡 API Integration Pattern

### Adding New API Endpoints

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

# Create router for feature
feature_router = APIRouter(prefix="/api/v1/feature", tags=["feature"])

# Dependency for common operations
async def get_user_context(user_id: str = Header(...)) -> dict:
    """Common dependency for user context"""
    # Validate user
    if not await validate_user(user_id):
        raise HTTPException(status_code=401, detail="Invalid user")
        
    # Get user mode
    mode = await get_neuros_mode(user_id)
    
    return {
        "user_id": user_id,
        "mode": mode,
        "tier_access": ["hot", "warm"]
    }

@feature_router.post("/process")
@track_metrics("feature_process")
async def process_feature(
    request: FeatureRequest,
    context: dict = Depends(get_user_context)
):
    """Process feature with full context"""
    # Track endpoint availability
    api_endpoint_availability.labels(
        endpoint="/api/v1/feature/process",
        method="POST"
    ).set(1.0)
    
    try:
        # Process based on mode
        processor = ModeAwareProcessor()
        result = await processor.process_with_mode(
            context["user_id"],
            request.dict()
        )
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        # Track endpoint failure
        api_endpoint_availability.labels(
            endpoint="/api/v1/feature/process",
            method="POST"
        ).set(0.0)
        raise

# Add router to main app
app.include_router(feature_router)
```

---

## 🔐 Security Integration Pattern

### Adding Authentication and Authorization

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

security = HTTPBearer()

class SecurityManager:
    """Pattern for security integration"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        
    async def verify_token(self, credentials: HTTPAuthorizationCredentials):
        """Verify JWT token"""
        token = credentials.credentials
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
                
            return user_id
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
            
    def create_access_token(self, user_id: str) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(hours=24)
        payload = {
            "sub": user_id,
            "exp": expire
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        return token

# Usage in endpoint
@app.post("/protected")
async def protected_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    security_mgr: SecurityManager = Depends(get_security_manager)
):
    user_id = await security_mgr.verify_token(credentials)
    # Process with authenticated user
```

---

## 📝 Testing Integration Pattern

### Adding Observability to Tests

```python
import pytest
from prometheus_client import CollectorRegistry, push_to_gateway

class TestMetricsCollector:
    """Collect metrics during tests"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self.test_requests = Counter(
            'test_requests_total',
            'Test requests',
            ['test_name', 'status'],
            registry=self.registry
        )
        
    def track_test(self, test_name: str, passed: bool):
        """Track test execution"""
        self.test_requests.labels(
            test_name=test_name,
            status="passed" if passed else "failed"
        ).inc()
        
    def push_metrics(self):
        """Push to Prometheus pushgateway"""
        push_to_gateway(
            'pushgateway:9091',
            job='integration_tests',
            registry=self.registry
        )

# Pytest fixture
@pytest.fixture(scope="session")
def metrics_collector():
    collector = TestMetricsCollector()
    yield collector
    collector.push_metrics()

# Usage in tests
@pytest.mark.asyncio
async def test_feature(metrics_collector):
    try:
        # Test logic
        result = await process_feature()
        assert result["status"] == "success"
        metrics_collector.track_test("test_feature", True)
    except Exception as e:
        metrics_collector.track_test("test_feature", False)
        raise
```

---

## 🏷️ Best Practices Summary

1. **Always Add Metrics**: Every new feature should export metrics
2. **Use Context Managers**: For automatic metric tracking
3. **Follow Naming Convention**: Use `auren_` prefix for all metrics
4. **Track Business Logic**: Not just technical metrics
5. **Add to Dashboards**: Update Grafana when adding metrics
6. **Document Metrics**: Add to METRICS_CATALOG.md
7. **Test Observability**: Include metric verification in tests
8. **Handle Errors Gracefully**: Track errors as metrics
9. **Consider Performance**: Use appropriate metric cardinality
10. **Update Documentation**: Keep this guide current

---

*This guide should be updated when new integration patterns are discovered or best practices evolve.* 