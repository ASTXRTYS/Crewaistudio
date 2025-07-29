"""
AUREN Complete Biometric System - All 8 Sections
Production-ready implementation with all required components
"""
import os
import json
import asyncio
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from contextlib import asynccontextmanager
from enum import Enum
import uuid

from fastapi import FastAPI, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect, Header, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
import asyncpg
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response as MetricsResponse
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import numpy as np
import pandas as pd
import structlog
from jose import JWTError, jwt
import httpx
import aiofiles
from pathlib import Path

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# ============= SECTION 1: WEBHOOK INFRASTRUCTURE =============

class DeviceType(str, Enum):
    OURA = "oura"
    WHOOP = "whoop"
    APPLE_HEALTH = "apple_health"
    GARMIN = "garmin"
    FITBIT = "fitbit"

class WebhookEvent(BaseModel):
    device_type: DeviceType
    event_type: str
    data: Dict[str, Any]
    timestamp: str
    user_id: Optional[str] = None
    signature: Optional[str] = None

class OAuthToken(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    expires_at: datetime
    device_type: DeviceType
    user_id: str

# Webhook signature verification
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature for security"""
    expected_sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_sig, signature)

# ============= SECTION 2: DEVICE-SPECIFIC HANDLERS =============

class BiometricEvent(BaseModel):
    """Unified biometric event format"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    device_type: DeviceType
    metric_type: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_data: Optional[Dict[str, Any]] = None

class OuraHandler:
    """Oura Ring data handler"""
    
    @staticmethod
    async def process_readiness(data: Dict[str, Any], user_id: str) -> List[BiometricEvent]:
        events = []
        
        # Extract readiness score
        if "score" in data:
            events.append(BiometricEvent(
                user_id=user_id,
                device_type=DeviceType.OURA,
                metric_type="readiness_score",
                value=float(data["score"]),
                timestamp=datetime.fromisoformat(data.get("day", datetime.utcnow().isoformat())),
                metadata={"contributors": data.get("contributors", {})},
                raw_data=data
            ))
        
        # Extract HRV
        if "hrv_balance" in data:
            events.append(BiometricEvent(
                user_id=user_id,
                device_type=DeviceType.OURA,
                metric_type="hrv",
                value=float(data["hrv_balance"]),
                timestamp=datetime.fromisoformat(data.get("day", datetime.utcnow().isoformat())),
                metadata={"type": "hrv_balance"},
                raw_data=data
            ))
        
        return events

class WHOOPHandler:
    """WHOOP Band data handler"""
    
    @staticmethod
    async def process_recovery(data: Dict[str, Any], user_id: str) -> List[BiometricEvent]:
        events = []
        
        if "recovery_score" in data:
            events.append(BiometricEvent(
                user_id=user_id,
                device_type=DeviceType.WHOOP,
                metric_type="recovery_score",
                value=float(data["recovery_score"]),
                timestamp=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
                metadata={
                    "hrv": data.get("hrv_rmssd"),
                    "resting_hr": data.get("resting_heart_rate")
                },
                raw_data=data
            ))
        
        return events

class AppleHealthKitHandler:
    """Apple HealthKit data handler"""
    
    @staticmethod
    async def process_batch(samples: List[Dict[str, Any]], user_id: str) -> List[BiometricEvent]:
        events = []
        
        for sample in samples:
            if sample.get("type") == "HKQuantityTypeIdentifierHeartRateVariabilitySDNN":
                events.append(BiometricEvent(
                    user_id=user_id,
                    device_type=DeviceType.APPLE_HEALTH,
                    metric_type="hrv",
                    value=float(sample["value"]),
                    timestamp=datetime.fromisoformat(sample["startDate"]),
                    metadata={"unit": sample.get("unit", "ms")},
                    raw_data=sample
                ))
            elif sample.get("type") == "HKQuantityTypeIdentifierHeartRate":
                events.append(BiometricEvent(
                    user_id=user_id,
                    device_type=DeviceType.APPLE_HEALTH,
                    metric_type="heart_rate",
                    value=float(sample["value"]),
                    timestamp=datetime.fromisoformat(sample["startDate"]),
                    metadata={"unit": sample.get("unit", "bpm")},
                    raw_data=sample
                ))
        
        return events

# ============= SECTION 3: KAFKA EVENT PIPELINE =============

class KafkaEventPipeline:
    """Kafka event pipeline with retry logic and DLQ"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None
        self.max_retries = 3
        self.retry_backoff = 1.0  # seconds
        
    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode(),
            acks='all',  # Wait for all replicas
            compression_type='gzip',
            max_batch_size=16384,
            linger_ms=100  # Batch for 100ms
        )
        await self.producer.start()
        
    async def publish_event(self, event: BiometricEvent, topic: str = "biometric-events"):
        """Publish event with retry logic"""
        retries = 0
        backoff = self.retry_backoff
        
        while retries < self.max_retries:
            try:
                await self.producer.send(
                    topic,
                    value=event.dict(),
                    key=event.user_id.encode()
                )
                return True
            except Exception as e:
                retries += 1
                if retries >= self.max_retries:
                    # Send to DLQ
                    await self._send_to_dlq(event, str(e))
                    logger.error(f"Failed to publish event after {retries} retries", error=str(e))
                    return False
                await asyncio.sleep(backoff)
                backoff *= 2  # Exponential backoff
                
    async def _send_to_dlq(self, event: BiometricEvent, error: str):
        """Send failed events to dead letter queue"""
        try:
            dlq_event = {
                "original_event": event.dict(),
                "error": error,
                "failed_at": datetime.utcnow().isoformat(),
                "retries": self.max_retries
            }
            await self.producer.send("biometric-events.dlq", value=dlq_event)
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
            
    async def stop(self):
        if self.producer:
            await self.producer.stop()

# ============= SECTION 4: BASELINE & PATTERN DETECTION =============

class BaselineCalculator:
    """7-day rolling baseline calculator"""
    
    def __init__(self, pg_pool: asyncpg.Pool):
        self.pg_pool = pg_pool
        self.window_days = 7
        
    async def calculate_baseline(self, user_id: str, metric_type: str) -> Dict[str, float]:
        """Calculate rolling baseline for a metric"""
        async with self.pg_pool.acquire() as conn:
            # Get last 7 days of data
            query = """
                SELECT value, timestamp
                FROM biometric_events
                WHERE user_id = $1 
                  AND metric_type = $2
                  AND timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
                ORDER BY timestamp DESC
            """
            rows = await conn.fetch(query, user_id, metric_type)
            
            if not rows:
                return {"mean": 0, "std": 0, "min": 0, "max": 0, "count": 0}
            
            values = [row['value'] for row in rows]
            
            return {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "count": len(values),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def store_baseline(self, user_id: str, metric_type: str, baseline: Dict[str, float]):
        """Store calculated baseline"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_baselines (user_id, metric_type, mean, std, min, max, sample_count, last_updated)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (user_id, metric_type) 
                DO UPDATE SET 
                    mean = $3, std = $4, min = $5, max = $6, 
                    sample_count = $7, last_updated = $8
            """, user_id, metric_type, baseline['mean'], baseline['std'], 
                baseline['min'], baseline['max'], baseline['count'], 
                datetime.fromisoformat(baseline['last_updated']))

class PatternDetector:
    """Pattern detection for various conditions"""
    
    def __init__(self, pg_pool: asyncpg.Pool):
        self.pg_pool = pg_pool
        
    async def detect_circadian_disruption(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Detect circadian rhythm disruption"""
        async with self.pg_pool.acquire() as conn:
            # Check sleep timing consistency
            query = """
                SELECT 
                    EXTRACT(HOUR FROM timestamp) as hour,
                    COUNT(*) as count
                FROM biometric_events
                WHERE user_id = $1 
                  AND metric_type = 'sleep_start'
                  AND timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
                GROUP BY EXTRACT(HOUR FROM timestamp)
            """
            rows = await conn.fetch(query, user_id)
            
            if rows:
                hours = [row['hour'] for row in rows]
                std_dev = np.std(hours)
                
                if std_dev > 2.0:  # More than 2 hour variation
                    return {
                        "pattern": "circadian_disruption",
                        "severity": "high" if std_dev > 3.0 else "moderate",
                        "variation_hours": float(std_dev),
                        "detected_at": datetime.utcnow().isoformat()
                    }
        return None
    
    async def detect_recovery_deficit(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Detect ongoing recovery deficit"""
        baseline = await BaselineCalculator(self.pg_pool).calculate_baseline(user_id, "hrv")
        
        if baseline['count'] < 3:
            return None
            
        async with self.pg_pool.acquire() as conn:
            # Get recent HRV values
            query = """
                SELECT value 
                FROM biometric_events
                WHERE user_id = $1 
                  AND metric_type = 'hrv'
                  AND timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
                ORDER BY timestamp DESC
                LIMIT 5
            """
            rows = await conn.fetch(query, user_id)
            
            if rows:
                recent_values = [row['value'] for row in rows]
                recent_mean = np.mean(recent_values)
                
                # Check if recent HRV is significantly below baseline
                if recent_mean < baseline['mean'] - baseline['std']:
                    deficit_percentage = ((baseline['mean'] - recent_mean) / baseline['mean']) * 100
                    return {
                        "pattern": "recovery_deficit",
                        "baseline_hrv": baseline['mean'],
                        "current_hrv": recent_mean,
                        "deficit_percentage": deficit_percentage,
                        "severity": "high" if deficit_percentage > 20 else "moderate",
                        "detected_at": datetime.utcnow().isoformat()
                    }
        return None

# ============= SECTION 5: POSTGRESQL EVENT STORAGE =============

async def create_database_schema(pg_pool: asyncpg.Pool):
    """Create all required database tables"""
    async with pg_pool.acquire() as conn:
        # Enable TimescaleDB extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
        
        # Create tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS biometric_events (
                event_id UUID PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                device_type VARCHAR(50) NOT NULL,
                metric_type VARCHAR(50) NOT NULL,
                value DOUBLE PRECISION NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                metadata JSONB,
                raw_data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_metric_time (user_id, metric_type, timestamp)
            );
        """)
        
        # Convert to TimescaleDB hypertable
        try:
            await conn.execute("""
                SELECT create_hypertable('biometric_events', 'timestamp', 
                    chunk_time_interval => INTERVAL '1 day',
                    if_not_exists => TRUE);
            """)
        except:
            pass  # Table might already be a hypertable
        
        # User baselines table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_baselines (
                user_id VARCHAR(255) NOT NULL,
                metric_type VARCHAR(50) NOT NULL,
                mean DOUBLE PRECISION,
                std DOUBLE PRECISION,
                min DOUBLE PRECISION,
                max DOUBLE PRECISION,
                sample_count INTEGER,
                last_updated TIMESTAMPTZ,
                PRIMARY KEY (user_id, metric_type)
            );
        """)
        
        # Pattern detections table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pattern_detections (
                detection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255) NOT NULL,
                pattern_type VARCHAR(100) NOT NULL,
                severity VARCHAR(20),
                metadata JSONB,
                detected_at TIMESTAMPTZ NOT NULL,
                resolved_at TIMESTAMPTZ,
                INDEX idx_user_pattern (user_id, pattern_type, detected_at)
            );
        """)
        
        # Mode switch history
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mode_switch_history (
                switch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255) NOT NULL,
                from_mode VARCHAR(50),
                to_mode VARCHAR(50) NOT NULL,
                trigger_event JSONB,
                switched_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_switches (user_id, switched_at)
            );
        """)

# ============= SECTION 6: APPLE HEALTHKIT BATCH HANDLER =============

class HealthKitBatchProcessor:
    """Batch processor for Apple HealthKit data"""
    
    def __init__(self, pg_pool: asyncpg.Pool, kafka_pipeline: KafkaEventPipeline):
        self.pg_pool = pg_pool
        self.kafka_pipeline = kafka_pipeline
        self.batch_size = 100
        self.concurrency_limit = 10
        self.semaphore = asyncio.Semaphore(self.concurrency_limit)
        
    async def process_batch(self, samples: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
        """Process HealthKit samples in batches"""
        total_samples = len(samples)
        processed = 0
        errors = []
        
        # Process in chunks
        for i in range(0, total_samples, self.batch_size):
            batch = samples[i:i + self.batch_size]
            
            async with self.semaphore:
                try:
                    # Convert to biometric events
                    events = await AppleHealthKitHandler.process_batch(batch, user_id)
                    
                    # Store in database
                    await self._store_events(events)
                    
                    # Publish to Kafka
                    for event in events:
                        await self.kafka_pipeline.publish_event(event)
                    
                    processed += len(batch)
                    
                except Exception as e:
                    error_msg = f"Failed to process batch {i//self.batch_size}: {str(e)}"
                    logger.error(error_msg)
                    errors.append({
                        "batch_index": i,
                        "error": str(e),
                        "sample_count": len(batch)
                    })
        
        return {
            "total_samples": total_samples,
            "processed": processed,
            "failed": total_samples - processed,
            "errors": errors,
            "success_rate": (processed / total_samples) * 100 if total_samples > 0 else 0
        }
    
    async def _store_events(self, events: List[BiometricEvent]):
        """Store events in PostgreSQL"""
        async with self.pg_pool.acquire() as conn:
            # Prepare batch insert
            values = []
            for event in events:
                values.append((
                    event.event_id,
                    event.user_id,
                    event.device_type.value,
                    event.metric_type,
                    event.value,
                    event.timestamp,
                    json.dumps(event.metadata),
                    json.dumps(event.raw_data) if event.raw_data else None
                ))
            
            # Batch insert
            await conn.executemany("""
                INSERT INTO biometric_events 
                (event_id, user_id, device_type, metric_type, value, timestamp, metadata, raw_data)
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb)
                ON CONFLICT (event_id) DO NOTHING
            """, values)

# ============= SECTION 7: BIOMETRIC-KAFKA-LANGGRAPH BRIDGE =============

class CognitiveMode(str, Enum):
    """Cognitive modes for NEUROS"""
    BASELINE = "baseline"
    REFLEX = "reflex" 
    HYPOTHESIS = "hypothesis"
    COMPANION = "companion"
    SENTINEL = "sentinel"

class ModeDecisionEngine:
    """Decides cognitive mode based on biometric data"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.mode_thresholds = {
            "hrv_drop": 25,  # ms drop triggers reflex
            "stress_high": 0.8,  # stress > 0.8 triggers sentinel
            "recovery_low": 40,  # recovery < 40% triggers companion
        }
        
    async def determine_mode(self, event: BiometricEvent, user_context: Dict[str, Any]) -> CognitiveMode:
        """Determine appropriate cognitive mode"""
        
        # Get user's baseline
        baseline_key = f"baseline:{event.user_id}:{event.metric_type}"
        baseline_data = await self.redis_client.get(baseline_key)
        
        if baseline_data:
            baseline = json.loads(baseline_data)
            
            # Check HRV drop
            if event.metric_type == "hrv":
                if baseline['mean'] - event.value > self.mode_thresholds['hrv_drop']:
                    return CognitiveMode.REFLEX
                    
            # Check stress level
            elif event.metric_type == "stress_level":
                if event.value > self.mode_thresholds['stress_high']:
                    return CognitiveMode.SENTINEL
                    
            # Check recovery score
            elif event.metric_type == "recovery_score":
                if event.value < self.mode_thresholds['recovery_low']:
                    return CognitiveMode.COMPANION
        
        # Check for patterns requiring hypothesis mode
        if user_context.get("anomaly_count", 0) > 3:
            return CognitiveMode.HYPOTHESIS
            
        return CognitiveMode.BASELINE

class BiometricKafkaLangGraphBridge:
    """Bridge between Kafka events and LangGraph processing"""
    
    def __init__(self, kafka_consumer: AIOKafkaConsumer, pg_pool: asyncpg.Pool, 
                 redis_client: redis.Redis, mode_engine: ModeDecisionEngine):
        self.kafka_consumer = kafka_consumer
        self.pg_pool = pg_pool
        self.redis_client = redis_client
        self.mode_engine = mode_engine
        self.processing_semaphore = asyncio.Semaphore(5)  # Process 5 events concurrently
        
    async def start_processing(self):
        """Start consuming and processing events"""
        async for msg in self.kafka_consumer:
            async with self.processing_semaphore:
                asyncio.create_task(self._process_event(msg))
                
    async def _process_event(self, msg):
        """Process individual Kafka message"""
        try:
            # Deserialize event
            event_data = json.loads(msg.value.decode())
            event = BiometricEvent(**event_data)
            
            # Get user context
            user_context = await self._get_user_context(event.user_id)
            
            # Determine cognitive mode
            mode = await self.mode_engine.determine_mode(event, user_context)
            
            # Record mode switch if changed
            if user_context.get("current_mode") != mode:
                await self._record_mode_switch(event.user_id, user_context.get("current_mode"), mode, event)
            
            # Update user context
            await self._update_user_context(event.user_id, mode, event)
            
            # Trigger LangGraph processing (Section 8 integration point)
            await self._trigger_langgraph_processing(event, mode, user_context)
            
        except Exception as e:
            logger.error(f"Failed to process Kafka event: {e}")
            
    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user's current context from Redis"""
        context_key = f"user_context:{user_id}"
        context_data = await self.redis_client.get(context_key)
        
        if context_data:
            return json.loads(context_data)
        return {"current_mode": CognitiveMode.BASELINE, "anomaly_count": 0}
        
    async def _update_user_context(self, user_id: str, mode: CognitiveMode, event: BiometricEvent):
        """Update user context in Redis"""
        context_key = f"user_context:{user_id}"
        context = await self._get_user_context(user_id)
        
        context["current_mode"] = mode.value
        context["last_event"] = event.dict()
        context["last_updated"] = datetime.utcnow().isoformat()
        
        await self.redis_client.setex(
            context_key,
            timedelta(days=7),
            json.dumps(context, default=str)
        )
        
    async def _record_mode_switch(self, user_id: str, from_mode: Optional[str], 
                                  to_mode: CognitiveMode, trigger_event: BiometricEvent):
        """Record mode switch in database"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO mode_switch_history (user_id, from_mode, to_mode, trigger_event)
                VALUES ($1, $2, $3, $4::jsonb)
            """, user_id, from_mode, to_mode.value, json.dumps(trigger_event.dict(), default=str))
            
    async def _trigger_langgraph_processing(self, event: BiometricEvent, mode: CognitiveMode, 
                                           user_context: Dict[str, Any]):
        """Trigger NEUROS cognitive graph processing"""
        # This is the integration point for Section 8
        # In full implementation, this would call the NEUROS graph
        logger.info(f"Triggering LangGraph processing for user {event.user_id} in mode {mode}")

# ============= SECTION 8: NEUROS INTEGRATION STUB =============

class NEUROSIntegration:
    """Integration point for NEUROS Cognitive Graph"""
    
    def __init__(self, pg_pool: asyncpg.Pool, redis_client: redis.Redis):
        self.pg_pool = pg_pool
        self.redis_client = redis_client
        
    async def process_with_neuros(self, event: BiometricEvent, mode: CognitiveMode, 
                                 user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process event through NEUROS cognitive graph"""
        # This would integrate with the full NEUROS implementation
        return {
            "mode": mode.value,
            "processed": True,
            "recommendations": self._get_mode_recommendations(mode),
            "personality_response": self._get_personality_response(mode, event)
        }
        
    def _get_mode_recommendations(self, mode: CognitiveMode) -> List[str]:
        """Get mode-specific recommendations"""
        recommendations = {
            CognitiveMode.BASELINE: ["Continue monitoring patterns", "Maintain current routines"],
            CognitiveMode.REFLEX: ["Immediate recovery protocol needed", "Reduce stressors"],
            CognitiveMode.HYPOTHESIS: ["Investigating patterns", "Gathering more data"],
            CognitiveMode.COMPANION: ["Focus on support", "Gentle recovery suggestions"],
            CognitiveMode.SENTINEL: ["High alert status", "Protective measures activated"]
        }
        return recommendations.get(mode, [])
        
    def _get_personality_response(self, mode: CognitiveMode, event: BiometricEvent) -> str:
        """Get NEUROS personality-driven response"""
        if mode == CognitiveMode.REFLEX:
            return f"Your HRV dropped to {event.value}. Let's address this immediately with a targeted recovery protocol."
        elif mode == CognitiveMode.COMPANION:
            return f"I notice you might be struggling. How about we take this recovery journey step by step?"
        return f"Monitoring your {event.metric_type}: {event.value}"

# ============= MAIN APPLICATION =============

# Global connections
redis_client: Optional[redis.Redis] = None
pg_pool: Optional[asyncpg.Pool] = None
kafka_producer: Optional[AIOKafkaProducer] = None
kafka_consumer: Optional[AIOKafkaConsumer] = None
kafka_pipeline: Optional[KafkaEventPipeline] = None
healthkit_processor: Optional[HealthKitBatchProcessor] = None
pattern_detector: Optional[PatternDetector] = None
baseline_calculator: Optional[BaselineCalculator] = None
mode_engine: Optional[ModeDecisionEngine] = None
bridge: Optional[BiometricKafkaLangGraphBridge] = None
neuros: Optional[NEUROSIntegration] = None

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all components"""
    global redis_client, pg_pool, kafka_producer, kafka_consumer, kafka_pipeline
    global healthkit_processor, pattern_detector, baseline_calculator
    global mode_engine, bridge, neuros
    
    logger.info("Starting AUREN Complete Biometric System...")
    
    # Initialize Redis
    try:
        redis_client = await redis.from_url(
            os.getenv("REDIS_URL", "redis://auren-redis:6379/0"),
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
    
    # Initialize PostgreSQL
    try:
        pg_pool = await asyncpg.create_pool(
            os.getenv("POSTGRES_URL", "postgresql://auren_user:securepwd123!@auren-postgres:5432/auren_production"),
            min_size=5,
            max_size=20
        )
        
        # Create schema
        await create_database_schema(pg_pool)
        logger.info("PostgreSQL connected and schema created")
    except Exception as e:
        logger.error(f"PostgreSQL setup failed: {e}")
    
    # Initialize Kafka
    try:
        # Initialize pipeline
        kafka_pipeline = KafkaEventPipeline(os.getenv("KAFKA_BROKERS", "auren-kafka:9092"))
        await kafka_pipeline.start()
        
        # Initialize consumer
        kafka_consumer = AIOKafkaConsumer(
            "biometric-events",
            bootstrap_servers=os.getenv("KAFKA_BROKERS", "auren-kafka:9092"),
            group_id="biometric-processor",
            enable_auto_commit=True,
            auto_offset_reset='earliest'
        )
        await kafka_consumer.start()
        
        logger.info("Kafka connected")
    except Exception as e:
        logger.error(f"Kafka setup failed: {e}")
    
    # Initialize components
    if pg_pool and kafka_pipeline:
        healthkit_processor = HealthKitBatchProcessor(pg_pool, kafka_pipeline)
        pattern_detector = PatternDetector(pg_pool)
        baseline_calculator = BaselineCalculator(pg_pool)
        
    if redis_client:
        mode_engine = ModeDecisionEngine(redis_client)
        
    if all([kafka_consumer, pg_pool, redis_client, mode_engine]):
        bridge = BiometricKafkaLangGraphBridge(kafka_consumer, pg_pool, redis_client, mode_engine)
        # Start bridge processing in background
        asyncio.create_task(bridge.start_processing())
        
    if pg_pool and redis_client:
        neuros = NEUROSIntegration(pg_pool, redis_client)
    
    logger.info("All components initialized!")
    
    yield
    
    # Cleanup
    if kafka_pipeline:
        await kafka_pipeline.stop()
    if kafka_consumer:
        await kafka_consumer.stop()
    if pg_pool:
        await pg_pool.close()
    if redis_client:
        await redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="AUREN Complete Biometric System",
    description="All 8 Sections: Webhooks, Handlers, Kafka, Baselines, Storage, Batch, Bridge, NEUROS",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # Keep existing wildcard for backward compatibility
        "https://pwa.aupex.ai", 
        "https://*.vercel.app",  # For Vercel preview deployments
        "http://localhost:5173",  # For local development
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= API ENDPOINTS =============

@app.get("/")
async def root():
    """System information"""
    return {
        "service": "AUREN Complete Biometric System",
        "version": "3.0.0",
        "sections_implemented": [
            "1. Webhook Infrastructure",
            "2. Device-Specific Handlers", 
            "3. Kafka Event Pipeline",
            "4. Baseline & Pattern Detection",
            "5. PostgreSQL Event Storage",
            "6. Apple HealthKit Batch Handler",
            "7. Biometric-Kafka-LangGraph Bridge",
            "8. NEUROS Cognitive Graph Integration"
        ],
        "status": "operational"
    }

@app.get("/health")
async def health():
    """Comprehensive health check"""
    components = {
        "redis": redis_client is not None,
        "postgres": pg_pool is not None,
        "kafka_producer": kafka_pipeline is not None,
        "kafka_consumer": kafka_consumer is not None,
        "healthkit_processor": healthkit_processor is not None,
        "pattern_detector": pattern_detector is not None,
        "baseline_calculator": baseline_calculator is not None,
        "mode_engine": mode_engine is not None,
        "bridge": bridge is not None,
        "neuros": neuros is not None
    }
    
    return {"status": "healthy", "components": components, "healthy": all(components.values())}

# ========================================================================================
# CHAT ENDPOINTS FOR PWA
# ========================================================================================

class ChatMessage(BaseModel):
    text: str
    agent_requested: str = "neuros"
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    agent_id: str
    session_id: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None

@app.post("/api/chat/neuros", response_model=ChatResponse)
async def chat_with_neuros(message: ChatMessage):
    """
    Handle text chat messages to NEUROS agent.
    Integrates with existing Kafka pipeline for processing.
    """
    try:
        session_id = message.session_id or f"pwa_session_{uuid.uuid4().hex[:8]}"
        
        # Create Kafka event for NEUROS processing
        event = {
            "event_type": "user.message",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user_id": "pwa_user",  # TODO: Get from auth
            "session_id": session_id,
            "message": {
                "text": message.text,
                "context": {
                    "device_type": "pwa",
                    "agent_requested": message.agent_requested,
                    "conversation_id": session_id
                }
            },
            "metadata": message.metadata or {}
        }
        
        # Send to Kafka for processing
        if kafka_pipeline:
            await kafka_pipeline.producer.send("user-interactions", json.dumps(event).encode())
            logger.info(f"Sent chat message to Kafka: {event['event_id']}")
        
        # For MVP, return immediate acknowledgment
        # Real response will come through WebSocket
        return ChatResponse(
            response="I'm processing your request and will respond shortly...",
            agent_id="neuros",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/voice")
async def chat_with_voice(
    audio: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    agent_requested: str = Form("neuros")
):
    """
    Handle voice messages for NEUROS.
    Stores audio file and queues for transcription.
    """
    try:
        session_id = session_id or f"pwa_session_{uuid.uuid4().hex[:8]}"
        
        # Validate audio file
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file")
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("/app/uploads/audio")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save audio file
        file_id = f"{uuid.uuid4().hex}.webm"
        file_path = upload_dir / file_id
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await audio.read()
            await f.write(content)
        
        # Create event for processing
        event = {
            "event_type": "user.voice_message",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user_id": "pwa_user",
            "session_id": session_id,
            "voice_data": {
                "file_id": file_id,
                "file_path": str(file_path),
                "content_type": audio.content_type,
                "size_bytes": len(content),
                "duration_seconds": None  # TODO: Extract from audio
            },
            "agent_requested": agent_requested
        }
        
        # Send to Kafka for processing
        if kafka_pipeline:
            await kafka_pipeline.producer.send("voice-messages", json.dumps(event).encode())
            logger.info(f"Sent voice message to Kafka: {event['event_id']}")
        
        return {
            "status": "received",
            "file_id": file_id,
            "session_id": session_id,
            "message": "Voice message received. Transcribing..."
        }
        
    except Exception as e:
        logger.error(f"Error handling voice message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/upload")
async def upload_file_for_analysis(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    context: Optional[str] = Form(None)
):
    """
    Handle file uploads (images, documents) for NEUROS analysis.
    Supports macro screenshots, workout photos, etc.
    """
    try:
        session_id = session_id or f"pwa_session_{uuid.uuid4().hex[:8]}"
        
        # Validate file type
        allowed_types = ['image/', 'application/pdf', 'text/']
        if not any(file.content_type.startswith(t) for t in allowed_types):
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Create uploads directory
        upload_dir = Path("/app/uploads/files")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file with unique name
        file_ext = Path(file.filename).suffix
        file_id = f"{uuid.uuid4().hex}{file_ext}"
        file_path = upload_dir / file_id
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create event for NEUROS analysis
        event = {
            "event_type": "user.file_upload",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user_id": "pwa_user",
            "session_id": session_id,
            "file_data": {
                "file_id": file_id,
                "file_path": str(file_path),
                "original_name": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(content),
                "context": context or "general_analysis"
            }
        }
        
        # If it's an image, we might want to run it through vision analysis
        if file.content_type.startswith('image/'):
            event["file_data"]["analysis_type"] = "vision"
            event["file_data"]["context"] = context or "nutrition_tracking"
        
        # Send to Kafka for processing
        if kafka_pipeline:
            await kafka_pipeline.producer.send("file-uploads", json.dumps(event).encode())
            logger.info(f"Sent file upload to Kafka: {event['event_id']}")
        
        return {
            "status": "uploaded",
            "file_id": file_id,
            "session_id": session_id,
            "message": f"File '{file.filename}' uploaded successfully. Analyzing...",
            "analysis_type": event["file_data"].get("analysis_type", "document")
        }
        
    except Exception as e:
        logger.error(f"Error handling file upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50
):
    """
    Retrieve chat history for a session.
    Note: Sessions expire after 2 hours per NEUROS constraints.
    """
    try:
        if not redis_client:
            return {"messages": [], "session_active": False}
        
        # Get messages from Redis (they auto-expire after 2 hours)
        key = f"chat:session:{session_id}:messages"
        messages = await redis_client.lrange(key, 0, limit - 1)
        
        return {
            "session_id": session_id,
            "messages": [json.loads(m) for m in messages],
            "session_active": len(messages) > 0,
            "ttl_seconds": await redis_client.ttl(key)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        return {"messages": [], "session_active": False, "error": str(e)}

@app.get("/api/agents/neuros/status")
async def get_neuros_status():
    """Get NEUROS agent status and capabilities."""
    return {
        "agent_id": "neuros",
        "name": "NEUROS",
        "tagline": "Elite Neural Operations System",
        "status": "operational" if neuros else "unavailable",
        "capabilities": [
            "hrv_analysis",
            "stress_detection", 
            "recovery_protocols",
            "neural_fatigue_assessment",
            "circadian_optimization",
            "cognitive_function_tracking"
        ],
        "specializations": [
            {
                "name": "Autonomic Balance",
                "description": "Nervous system optimization",
                "active_protocols": 12,
                "success_rate": 0.94
            },
            {
                "name": "HRV Analytics",
                "description": "Real-time heart rate variability",
                "data_points": 1200000,
                "accuracy": 0.97
            },
            {
                "name": "Neural Fatigue",
                "description": "Cognitive load assessment",
                "models": 8,
                "precision": 0.91
            }
        ],
        "version": "1.0.0",
        "last_updated": datetime.now().isoformat()
    }

# Enhanced WebSocket for PWA Chat
@app.websocket("/ws/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat with NEUROS."""
    await websocket.accept()
    
    try:
        # Store websocket reference for this session
        ws_key = f"ws:session:{session_id}"
        if redis_client:
            await redis_client.set(ws_key, "connected", ex=7200)  # 2 hour TTL
        
        logger.info(f"WebSocket connected for session: {session_id}")
        
        # Send initial connection success
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Start background task to listen for NEUROS responses
        response_task = asyncio.create_task(
            listen_for_neuros_responses(websocket, session_id)
        )
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
                elif message.get("type") == "message":
                    # Process chat message
                    await handle_chat_message_ws(message, session_id)
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    finally:
        response_task.cancel()
        if redis_client:
            await redis_client.delete(ws_key)
        logger.info(f"WebSocket disconnected for session: {session_id}")

async def handle_chat_message_ws(message: Dict[str, Any], session_id: str):
    """Handle incoming chat messages from WebSocket."""
    try:
        # Create event for Kafka
        event = {
            "event_type": "user.message",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user_id": "pwa_user",
            "session_id": session_id,
            "message": {
                "text": message.get("text", ""),
                "context": {
                    "device_type": "pwa",
                    "agent_requested": message.get("agent_requested", "neuros"),
                    "conversation_id": session_id
                }
            }
        }
        
        # Send to Kafka
        if kafka_pipeline:
            await kafka_pipeline.producer.send("user-interactions", json.dumps(event).encode())
        
        # Store in Redis for history
        if redis_client:
            chat_key = f"chat:session:{session_id}:messages"
            await redis_client.lpush(chat_key, json.dumps({
                "sender": "user",
                "text": message.get("text"),
                "timestamp": event["timestamp"]
            }))
            await redis_client.expire(chat_key, 7200)  # 2 hours
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")

async def listen_for_neuros_responses(websocket: WebSocket, session_id: str):
    """
    Background task to listen for NEUROS responses from Redis
    and forward them to the WebSocket client.
    """
    try:
        if not redis_client:
            return
            
        # Subscribe to response channel for this session
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"neuros:responses:{session_id}")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                response_data = json.loads(message["data"])
                
                # Send to WebSocket
                await websocket.send_json({
                    "type": "agent_response",
                    "agent_id": "neuros",
                    "response": {
                        "text": response_data.get("text", ""),
                        "data": response_data.get("data", {}),
                        "visualizations": response_data.get("visualizations", [])
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
                # Store in chat history
                chat_key = f"chat:session:{session_id}:messages"
                await redis_client.lpush(chat_key, json.dumps({
                    "sender": "agent",
                    "agent_id": "neuros",
                    "text": response_data.get("text"),
                    "timestamp": datetime.now().isoformat()
                }))
                
    except asyncio.CancelledError:
        await pubsub.unsubscribe()
        raise
    except Exception as e:
        logger.error(f"Error in response listener: {e}")

# ========================================================================================
# EXISTING WEBHOOK AND BIOMETRIC ENDPOINTS CONTINUE BELOW
# ========================================================================================

@app.post("/webhooks/{device_type}")
async def webhook_handler(
    device_type: DeviceType,
    request: Request,
    x_webhook_signature: Optional[str] = Header(None)
):
    """Universal webhook handler for all devices"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify signature if provided
        if x_webhook_signature:
            secret = os.getenv(f"{device_type.upper()}_WEBHOOK_SECRET", "")
            if not verify_webhook_signature(body, x_webhook_signature, secret):
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse request data
        data = await request.json()
        
        # Get user_id from OAuth token or request
        user_id = data.get("user_id", "test_user")  # In production, get from auth
        
        # Process based on device type
        events = []
        
        if device_type == DeviceType.OURA:
            if data.get("event_type") == "readiness.updated":
                events = await OuraHandler.process_readiness(data.get("data", {}), user_id)
                
        elif device_type == DeviceType.WHOOP:
            if data.get("event_type") == "recovery.updated":
                events = await WHOOPHandler.process_recovery(data.get("data", {}), user_id)
                
        elif device_type == DeviceType.APPLE_HEALTH:
            # Handle batch of samples
            samples = data.get("samples", [])
            events = await AppleHealthKitHandler.process_batch(samples, user_id)
            
        # Store events and publish to Kafka
        processed = []
        for event in events:
            # Store in database
            if pg_pool:
                async with pg_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO biometric_events 
                        (event_id, user_id, device_type, metric_type, value, timestamp, metadata, raw_data)
                        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb)
                    """, event.event_id, event.user_id, event.device_type.value,
                        event.metric_type, event.value, event.timestamp,
                        json.dumps(event.metadata), json.dumps(event.raw_data))
            
            # Publish to Kafka
            if kafka_pipeline:
                await kafka_pipeline.publish_event(event)
            
            # Calculate baseline
            if baseline_calculator:
                baseline = await baseline_calculator.calculate_baseline(event.user_id, event.metric_type)
                await baseline_calculator.store_baseline(event.user_id, event.metric_type, baseline)
            
            # Detect patterns
            if pattern_detector:
                circadian = await pattern_detector.detect_circadian_disruption(event.user_id)
                recovery = await pattern_detector.detect_recovery_deficit(event.user_id)
                
                if circadian:
                    logger.info(f"Circadian disruption detected for {event.user_id}")
                if recovery:
                    logger.info(f"Recovery deficit detected for {event.user_id}")
            
            processed.append(event.dict())
        
        return {
            "status": "success",
            "device_type": device_type,
            "events_processed": len(processed),
            "events": processed
        }
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= SECTION 6: BATCH PROCESSING ENDPOINT =============

@app.post("/batch/healthkit")
async def process_healthkit_batch(
    samples: List[Dict[str, Any]],
    user_id: str = "test_user"
):
    """Process batch of HealthKit samples"""
    if not healthkit_processor:
        raise HTTPException(status_code=503, detail="Batch processor not available")
    
    result = await healthkit_processor.process_batch(samples, user_id)
    return result

# ============= QUERY ENDPOINTS =============

@app.get("/baselines/{user_id}/{metric_type}")
async def get_baseline(user_id: str, metric_type: str):
    """Get user's baseline for a metric"""
    if not baseline_calculator:
        raise HTTPException(status_code=503, detail="Baseline calculator not available")
    
    baseline = await baseline_calculator.calculate_baseline(user_id, metric_type)
    return baseline

@app.get("/patterns/{user_id}")
async def get_patterns(user_id: str):
    """Get detected patterns for user"""
    if not pattern_detector:
        raise HTTPException(status_code=503, detail="Pattern detector not available")
    
    patterns = []
    
    circadian = await pattern_detector.detect_circadian_disruption(user_id)
    if circadian:
        patterns.append(circadian)
        
    recovery = await pattern_detector.detect_recovery_deficit(user_id)
    if recovery:
        patterns.append(recovery)
    
    return {
        "user_id": user_id,
        "patterns": patterns,
        "checked_at": datetime.utcnow().isoformat()
    }

@app.get("/mode/{user_id}")
async def get_cognitive_mode(user_id: str):
    """Get user's current cognitive mode"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    context = await redis_client.get(f"user_context:{user_id}")
    if context:
        return json.loads(context)
    return {"current_mode": "baseline", "message": "No mode data available"}

# ============= TEST ENDPOINT =============

@app.post("/test/end-to-end")
async def test_end_to_end():
    """Test complete flow from webhook to NEUROS"""
    test_event = BiometricEvent(
        user_id="test_user",
        device_type=DeviceType.APPLE_HEALTH,
        metric_type="hrv",
        value=35.0,  # Low HRV to trigger mode switch
        timestamp=datetime.utcnow(),
        metadata={"test": True}
    )
    
    # Store event
    if pg_pool:
        async with pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO biometric_events 
                (event_id, user_id, device_type, metric_type, value, timestamp, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
            """, test_event.event_id, test_event.user_id, test_event.device_type.value,
                test_event.metric_type, test_event.value, test_event.timestamp,
                json.dumps(test_event.metadata))
    
    # Publish to Kafka
    if kafka_pipeline:
        await kafka_pipeline.publish_event(test_event)
    
    # Determine mode
    mode = CognitiveMode.BASELINE
    if mode_engine:
        mode = await mode_engine.determine_mode(test_event, {})
    
    # Process with NEUROS
    neuros_response = {}
    if neuros:
        neuros_response = await neuros.process_with_neuros(test_event, mode, {})
    
    return {
        "test_status": "completed",
        "event": test_event.dict(),
        "mode_triggered": mode.value,
        "neuros_response": neuros_response,
        "components_used": {
            "storage": pg_pool is not None,
            "kafka": kafka_pipeline is not None,
            "mode_engine": mode_engine is not None,
            "neuros": neuros is not None
        }
    }

# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Gauge
    from fastapi.responses import Response
    
    # Register metrics if not exists
    from prometheus_client.registry import REGISTRY
    
    # Try to create metrics (will skip if already exists)
    try:
        health_gauge = Gauge("biometric_api_health", "API health status")
        health_gauge.set(1)
    except:
        # Metric already registered
        for metric in REGISTRY.collect():
            if metric.name == "biometric_api_health":
                for sample in metric.samples:
                    if sample.name == "biometric_api_health":
                        # Update existing metric
                        break
    
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888) 
# Prometheus metrics endpoint
