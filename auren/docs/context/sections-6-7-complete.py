# =============================================================================
# SECTION 6: APPLE HEALTHKIT HANDLER WITH ENHANCED ERROR HANDLING
# =============================================================================

import structlog
from prometheus_client import Counter, Histogram, Gauge
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from kafka import KafkaProducer

# Note: The following are imported from earlier sections:
# - BiometricReading (dataclass)
# - BiometricEvent (dataclass)  
# - WearableType (Enum)
# These would be in a shared module in the actual implementation

# Try to import dateutil at module level
try:
    from dateutil import parser as date_parser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False
    import logging
    logging.warning("dateutil not available, using fallback timestamp parsing")

# Structured logging setup with trace_id support
logger = structlog.get_logger("auren.healthkit")

# Prometheus metrics
healthkit_samples_processed = Counter(
    'healthkit_samples_processed_total',
    'Total HealthKit samples processed',
    ['metric_type', 'status']
)
healthkit_batch_duration = Histogram(
    'healthkit_batch_processing_seconds',
    'Time spent processing HealthKit batches'
)
healthkit_conversion_errors = Counter(
    'healthkit_conversion_errors_total',
    'HealthKit sample conversion errors',
    ['error_type']
)

class AppleHealthKitHandler:
    """
    Enhanced Apple HealthKit handler with batch processing and observability
    
    Since HealthKit doesn't have webhooks, this handles data pushed
    from an iOS companion app with efficient batch processing.
    """
    
    def __init__(self, kafka_producer: KafkaProducer, config: Optional[Dict[str, Any]] = None):
        self.kafka_producer = kafka_producer
        self.batch_size = 100  # Process in batches
        self.config = config or {}
        
        # Load metrics from config or use defaults
        self.supported_metrics = self.config.get('supported_metrics', {
            "heartRate": "heart_rate",
            "heartRateVariabilitySDNN": "hrv",
            "restingHeartRate": "resting_heart_rate",
            "walkingHeartRateAverage": "walking_heart_rate",
            "oxygenSaturation": "blood_oxygen",
            "bodyTemperature": "body_temperature",
            "respiratoryRate": "respiratory_rate",
            "bloodPressureSystolic": "blood_pressure_systolic",
            "bloodPressureDiastolic": "blood_pressure_diastolic",
            "activeEnergyBurned": "active_calories",
            "stepCount": "steps",
            "distanceWalkingRunning": "distance_meters",
            "flightsClimbed": "flights_climbed",
            "appleExerciseTime": "exercise_minutes",
            "appleStandTime": "stand_minutes",
            "sleepAnalysis": "sleep_state",
            "mindfulSession": "mindful_minutes"
        })
        
        # Batch processing stats
        self.batch_stats = {
            "total_processed": 0,
            "conversion_errors": 0,
            "unknown_metrics": 0,
            "malformed_timestamps": 0
        }
    
    async def handle_healthkit_push(self, data: dict) -> Optional[BiometricEvent]:
        """
        Process single HealthKit data push with enhanced error tracking
        
        The iOS app should send data in this format:
        {
            "user_id": "string",
            "samples": [
                {
                    "type": "heartRate",
                    "value": 72,
                    "timestamp": "2025-01-27T10:30:00Z",
                    "unit": "bpm",
                    "source": "Apple Watch"
                }
            ]
        }
        """
        try:
            user_id = data.get("user_id")
            samples = data.get("samples", [])
            
            if not user_id or not samples:
                logger.warning(
                    "invalid_healthkit_data",
                    user_id=user_id,
                    sample_count=len(samples),
                    reason="missing_required_fields"
                )
                return None
            
            # Convert samples to readings with error tracking
            readings = []
            latest_timestamp = None
            conversion_errors = 0
            
            for i, sample in enumerate(samples):
                try:
                    reading = self._convert_sample_to_reading(sample)
                    if reading:
                        readings.append(reading)
                        if not latest_timestamp or reading.timestamp > latest_timestamp:
                            latest_timestamp = reading.timestamp
                        # Map to safe metric type for Prometheus
                        safe_metric_type = self.supported_metrics.get(
                            sample.get("type", "unknown"), 
                            "unsupported"
                        )
                        healthkit_samples_processed.labels(
                            metric_type=safe_metric_type,
                            status="success"
                        ).inc()
                    else:
                        conversion_errors += 1
                        # Map to safe metric type for Prometheus
                        safe_metric_type = self.supported_metrics.get(
                            sample.get("type", "unknown"), 
                            "unsupported"
                        )
                        healthkit_samples_processed.labels(
                            metric_type=safe_metric_type,
                            status="failed"
                        ).inc()
                except Exception as e:
                    conversion_errors += 1
                    logger.error(
                        "sample_conversion_error",
                        user_id=user_id,
                        sample_index=i,
                        sample_type=sample.get("type"),
                        error=str(e)
                    )
                    healthkit_conversion_errors.labels(error_type=type(e).__name__).inc()
            
            if not readings:
                logger.warning(
                    "no_valid_readings",
                    user_id=user_id,
                    total_samples=len(samples),
                    conversion_errors=conversion_errors
                )
                return None
            
            # Log conversion success rate
            success_rate = len(readings) / len(samples) if samples else 0
            logger.info(
                "healthkit_push_processed",
                user_id=user_id,
                total_samples=len(samples),
                valid_readings=len(readings),
                success_rate=success_rate,
                conversion_errors=conversion_errors
            )
            
            return BiometricEvent(
                device_type=WearableType.APPLE_HEALTH,
                user_id=user_id,
                timestamp=latest_timestamp or datetime.now(timezone.utc),
                readings=readings
            )
            
        except Exception as e:
            logger.error(
                "healthkit_processing_failed",
                user_id=data.get("user_id", "unknown"),
                error=str(e),
                error_type=type(e).__name__
            )
            return BiometricEvent(
                device_type=WearableType.APPLE_HEALTH,
                user_id=data.get("user_id", "unknown"),
                timestamp=datetime.now(timezone.utc),
                readings=[]
            )
    
    async def handle_healthkit_batch(self, batch_data: List[dict]) -> List[BiometricEvent]:
        """
        Process batch of HealthKit data efficiently with metrics
        
        Used when iOS app sends accumulated data
        """
        with healthkit_batch_duration.time():
            events = []
            batch_start_time = datetime.now()
            
            # Local batch stats to avoid race conditions
            batch_stats = {
                "total_processed": 0,
                "conversion_errors": 0,
                "unknown_metrics": 0,
                "malformed_timestamps": 0
            }
            
            # Store original batch_stats and restore after
            original_stats = self.batch_stats
            self.batch_stats = batch_stats
            
            try:
                # Process in parallel using asyncio
                tasks = []
                
                # Create coroutine INSIDE semaphore acquisition
                semaphore = asyncio.Semaphore(10)
                
                async def process_with_semaphore(data):
                    """Create coroutine INSIDE semaphore acquisition"""
                    async with semaphore:
                        return await self.handle_healthkit_push(data)
                
                # Create tasks with semaphore
                for data in batch_data:
                    task = process_with_semaphore(data)
                    tasks.append(task)
                
                results = await asyncio.gather(
                    *tasks,
                    return_exceptions=True
                )
                
                # Filter out exceptions and None results
                for result in results:
                    if isinstance(result, BiometricEvent):
                        events.append(result)
                        batch_stats["total_processed"] += 1
                    elif isinstance(result, Exception):
                        batch_stats["conversion_errors"] += 1
                        logger.error(
                            "batch_processing_error",
                            error=str(result),
                            error_type=type(result).__name__
                        )
                
                # Log batch-level stats for observability
                batch_duration = (datetime.now() - batch_start_time).total_seconds()
                logger.info(
                    "healthkit_batch_completed",
                    batch_size=len(batch_data),
                    successful_events=len(events),
                    total_processed=batch_stats["total_processed"],
                    conversion_errors=batch_stats["conversion_errors"],
                    unknown_metrics=batch_stats["unknown_metrics"],
                    malformed_timestamps=batch_stats["malformed_timestamps"],
                    duration_seconds=batch_duration,
                    events_per_second=len(events) / batch_duration if batch_duration > 0 else 0
                )
                
                # Alert if error rate is too high
                error_rate = batch_stats["conversion_errors"] / len(batch_data) if batch_data else 0
                if error_rate > 0.1:  # More than 10% errors
                    logger.warning(
                        "high_error_rate",
                        error_rate=error_rate,
                        conversion_errors=batch_stats["conversion_errors"],
                        batch_size=len(batch_data)
                    )
                
            finally:
                # Restore original batch_stats
                self.batch_stats = original_stats
                
            return events
    
    def _convert_sample_to_reading(self, sample: dict) -> Optional[BiometricReading]:
        """Convert HealthKit sample to BiometricReading with robust error handling"""
        try:
            sample_type = sample.get("type")
            value = sample.get("value")
            timestamp_str = sample.get("timestamp")
            
            if not all([sample_type, value is not None, timestamp_str]):
                logger.debug(
                    "incomplete_sample",
                    sample_type=sample_type,
                    has_value=value is not None,
                    has_timestamp=timestamp_str is not None
                )
                return None
            
            # Check if we support this metric
            if sample_type not in self.supported_metrics:
                self.batch_stats["unknown_metrics"] += 1
                logger.debug(
                    "unsupported_metric",
                    metric_type=sample_type,
                    supported_metrics=list(self.supported_metrics.keys())
                )
                healthkit_conversion_errors.labels(error_type="unknown_metric").inc()
                return None
            
            metric_name = self.supported_metrics[sample_type]
            
            # Parse timestamp with dateutil for maximum compatibility
            timestamp = None
            if HAS_DATEUTIL:
                try:
                    timestamp = date_parser.isoparse(timestamp_str)
                except Exception as e:
                    self.batch_stats["malformed_timestamps"] += 1
                    logger.warning(
                        "dateutil_parse_failed",
                        timestamp_str=timestamp_str,
                        error=str(e)
                    )
            
            # Fallback to manual parsing if dateutil failed or not available
            if not timestamp:
                for fmt in [
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S%z"
                ]:
                    try:
                        if fmt.endswith('Z') and timestamp_str.endswith('Z'):
                            # Handle both 3 and 6 digit fractional seconds
                            if '.' in timestamp_str:
                                # Normalize fractional seconds to 6 digits
                                parts = timestamp_str[:-1].split('.')
                                frac = parts[1].ljust(6, '0')[:6]
                                normalized = f"{parts[0]}.{frac}+00:00"
                                timestamp = datetime.fromisoformat(normalized)
                            else:
                                timestamp_str_parsed = timestamp_str[:-1] + '+00:00'
                                timestamp = datetime.fromisoformat(timestamp_str_parsed)
                        else:
                            timestamp = datetime.strptime(timestamp_str, fmt)
                        
                        # Make naive timestamps aware
                        if timestamp.tzinfo is None:
                            timestamp = timestamp.replace(tzinfo=timezone.utc)
                        break
                    except:
                        continue
            
            if not timestamp:
                self.batch_stats["malformed_timestamps"] += 1
                logger.warning(
                    "malformed_timestamp",
                    timestamp_str=timestamp_str,
                    sample_type=sample_type
                )
                healthkit_conversion_errors.labels(error_type="malformed_timestamp").inc()
                timestamp = datetime.now(timezone.utc)
            
            # Determine confidence based on source
            source = sample.get("source", "").lower()
            if "apple watch" in source:
                confidence = 1.0
            elif "iphone" in source:
                confidence = 0.8
            else:
                confidence = 0.7
            
            # Special handling for body temperature
            if sample_type == "bodyTemperature":
                # Convert to Celsius if needed BEFORE validation
                value = self._convert_temperature_if_needed(float(value))
            
            # Special handling for sleep analysis
            if sample_type == "sleepAnalysis":
                # Convert sleep state to numeric value
                sleep_states = {
                    "InBed": 0,
                    "Asleep": 1,
                    "AsleepCore": 2,
                    "AsleepDeep": 3,
                    "AsleepREM": 4
                }
                value = sleep_states.get(value, 0)
            
            # Convert to float after any transformations
            value = float(value)
            
            # Validate value range based on metric type
            if not self._validate_value_range(metric_name, value):
                logger.warning(
                    "value_out_of_range",
                    metric=metric_name,
                    value=value,
                    sample_type=sample_type
                )
                healthkit_conversion_errors.labels(error_type="invalid_value").inc()
                return None
            
            return BiometricReading(
                metric=metric_name,
                value=value,
                timestamp=timestamp,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(
                "sample_conversion_failed",
                sample=sample,
                error=str(e),
                error_type=type(e).__name__
            )
            # Guard Prometheus label cardinality - truncate long exception names
            safe_error_type = type(e).__name__[:32]
            healthkit_conversion_errors.labels(error_type=safe_error_type).inc()
            return None
    
    def _convert_temperature_if_needed(self, value: float) -> float:
        """Convert temperature from Fahrenheit to Celsius if needed"""
        if value > 45:  # Likely Fahrenheit
            original_value = value
            converted_value = (value - 32) * 5/9
            logger.debug(
                "temperature_unit_conversion",
                original_value=original_value,
                converted_value=converted_value,
                assumed_unit="fahrenheit"
            )
            return converted_value
        return value
    
    def _validate_value_range(self, metric: str, value: Any) -> bool:
        """Validate that biometric values are within reasonable ranges"""
        try:
            value = float(value)
        except:
            return False
            
        # Define reasonable ranges for each metric
        ranges = {
            "heart_rate": (20, 250),
            "hrv": (0, 300),
            "blood_oxygen": (70, 100),
            "body_temperature": (35, 42),  # Celsius
            "respiratory_rate": (5, 40),
            "blood_pressure_systolic": (70, 200),
            "blood_pressure_diastolic": (40, 130),
            "steps": (0, 100000),
            "distance_meters": (0, 50000),
            "active_calories": (0, 5000),
            "exercise_minutes": (0, 1440),  # Max 24 hours
            "sleep_state": (0, 4)
        }
        
        if metric in ranges:
            min_val, max_val = ranges[metric]
            return min_val <= value <= max_val
        
        # For unknown metrics, accept any positive value
        return value >= 0
    
    def aggregate_readings(self, readings: List[BiometricReading]) -> Dict[str, BiometricReading]:
        """
        Aggregate multiple readings of the same metric
        
        Used when iOS app sends multiple samples of the same type
        """
        aggregated = {}
        
        for reading in readings:
            if reading.metric not in aggregated:
                aggregated[reading.metric] = reading
            else:
                # Keep the most recent reading with highest confidence
                existing = aggregated[reading.metric]
                if (reading.timestamp > existing.timestamp or 
                    (reading.timestamp == existing.timestamp and 
                     reading.confidence > existing.confidence)):
                    aggregated[reading.metric] = reading
        
        return aggregated

# =============================================================================
# SECTION 7: KAFKA-LANGGRAPH BRIDGE WITH CHECKPOINTING
# =============================================================================

import yaml
import asyncio
import json
import structlog
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, AsyncRetrying
from prometheus_client import Counter, Histogram, Gauge, Summary
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import deque
from typing import Optional, Dict, Any, List
import asyncpg
import redis

# Note: The following are imported from earlier sections:
# - BiometricEvent, BiometricReading (dataclasses)
# - NEUROSState (TypedDict)
# - CognitiveMode (Enum)
# - CompiledGraph (from langgraph)
# - PostgresSaver (from langgraph.checkpoint.postgres)
# - SystemMessage, HumanMessage (from langchain_core.messages)
# - KafkaProducer, KafkaConsumer (from kafka)

# Structured logging
logger = structlog.get_logger("auren.kafka_bridge")

# Prometheus metrics
kafka_messages_processed = Counter(
    'kafka_messages_processed_total',
    'Total Kafka messages processed',
    ['status']
)
kafka_consumer_lag = Gauge(
    'kafka_consumer_lag_messages',
    'Current Kafka consumer lag'
)
mode_switches_total = Counter(
    'mode_switches_total',
    'Total cognitive mode switches',
    ['from_mode', 'to_mode', 'reason']
)
checkpoint_save_duration = Histogram(
    'checkpoint_save_seconds',
    'Time to save checkpoint'
)
redis_operation_duration = Summary(
    'redis_operation_seconds',
    'Redis operation duration',
    ['operation']
)
checkpoint_queue_full_total = Counter(
    'checkpoint_queue_full_total',
    'Times checkpoint queue reached max capacity'
)

# Load configuration
def load_biometric_config(config_path: str = "config/biometric_thresholds.yaml") -> dict:
    """Load biometric thresholds from configuration file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(
            "config_load_failed",
            config_path=config_path,
            error=str(e),
            action="using_defaults"
        )
        # Return default configuration
        return {
            "thresholds": {
                "hrv_drop_ms": 25,
                "hrv_drop_percentage": 30,
                "heart_rate_elevated": 100,
                "heart_rate_elevation": 20,
                "stress_level_high": 0.7,
                "stress_level_critical": 0.85,
                "recovery_score_low": 40,
                "recovery_score_moderate": 60,
                "mode_switch_cooldown_seconds": 300
            },
            "baselines": {
                "hrv_default": 60,
                "heart_rate_default": 70,
                "recovery_score_default": 75
            }
        }

# Hot-reload configuration without restart
async def reload_config(bridge: 'BiometricKafkaLangGraphBridge', config_path: str):
    """Hot-reload configuration for threshold tuning"""
    try:
        new_config = load_biometric_config(config_path)
        bridge.config = new_config
        bridge.thresholds = new_config["thresholds"]
        bridge.baselines = new_config["baselines"]
        logger.info(
            "config_reloaded",
            thresholds=bridge.thresholds,
            config_path=config_path
        )
        return True
    except Exception as e:
        logger.error(
            "config_reload_failed",
            error=str(e),
            config_path=config_path
        )
        return False

class BiometricKafkaLangGraphBridge:
    """
    Enhanced bridge with PostgreSQL checkpointing, concurrent processing,
    and production monitoring
    
    This is the HEART of the biometric awareness system!
    """
    
    def __init__(self, graph: CompiledGraph, kafka_config: dict, 
                 postgres_pool: asyncpg.Pool, redis_client: redis.Redis,
                 max_concurrent_events: int = 50, config_path: Optional[str] = None):
        self.graph = graph
        self.kafka_config = kafka_config
        self.postgres_pool = postgres_pool
        self.redis_client = redis_client
        self.max_concurrent_events = max_concurrent_events
        
        # Load configuration
        self.config = load_biometric_config(config_path) if config_path else load_biometric_config()
        self.thresholds = self.config["thresholds"]
        self.baselines = self.config["baselines"]
        
        # Initialize checkpoint system with batching
        self.checkpointer = PostgresSaver(postgres_pool)
        self.checkpoint_queue = deque(maxlen=1000)  # Buffer checkpoints
        self.last_checkpoint_flush = datetime.now()
        self.checkpoint_interval_seconds = 30  # Batch checkpoints every 30s
        
        # Thread executor for blocking I/O
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="kafka")
        self.consumer_thread = None
        self.consumer_lock = threading.Lock()
        
        # Kafka setup
        self.consumer = None
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=3,
            retry_backoff_ms=1000,
            compression_type='gzip',  # Compress for better throughput
            linger_ms=100,  # Batch messages for efficiency
            batch_size=16384  # 16KB batches
        )
        
        # State management
        self.running = False
        self.active_sessions = {}  # user_id -> session_id mapping
        self.processing_semaphore = asyncio.Semaphore(max_concurrent_events)
        
        # State size limits
        self.max_messages_per_state = 100  # Rolling window
        self.max_mode_history = 50  # Keep recent mode switches
        
        # Checkpoint batching
        self.pending_checkpoints = {}  # session_id -> pending_state
        self.max_pending_checkpoints = 5000  # Prevent unbounded growth
        self.significant_change_thresholds = {
            "hrv": 5,  # ms
            "heart_rate": 10,  # bpm
            "stress_level": 0.1  # 10% change
        }
        
        # Metrics
        self.events_processed = 0
        self.mode_switches = 0
        self.errors_count = 0
        self.start_time = datetime.now()
        
        # Health check endpoint data
        self.last_checkpoint_latency = 0
        self.last_redis_check = datetime.now()
    
    async def _poll_kafka_in_thread(self, timeout_ms: int = 1000):
        """Poll Kafka in thread executor to avoid blocking event loop"""
        loop = asyncio.get_running_loop()
        
        def _blocking_poll():
            with self.consumer_lock:
                if self.consumer:
                    return self.consumer.poll(timeout_ms=timeout_ms)
                return {}
        
        # Run blocking poll in thread
        return await loop.run_in_executor(self.executor, _blocking_poll)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=AsyncRetrying,  # Explicit async retry
        reraise=True
    )
    async def _poll_with_retry(self, timeout_ms: int = 1000):
        """Poll Kafka with retry logic for network hiccups"""
        try:
            return await self._poll_kafka_in_thread(timeout_ms)
        except Exception as e:
            logger.warning(
                "kafka_poll_failed",
                error=str(e),
                action="retrying"
            )
            raise
    
    async def start_consuming(self):
        """
        Enhanced consumer with concurrent processing, checkpointing, and crash recovery
        """
        self.running = True
        
        # Create consumer with optimized settings
        self.consumer = KafkaConsumer(
            'biometric-events',
            bootstrap_servers=self.kafka_config['bootstrap_servers'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='neuros-cognitive-processor',
            enable_auto_commit=False,  # Manual commit for reliability
            auto_offset_reset='latest',
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000,
            max_poll_records=100,  # Process in batches
            fetch_min_bytes=1024,  # Optimize network usage
            fetch_max_wait_ms=500  # Balance latency vs throughput
        )
        
        # Check for crash recovery - seek to last committed offset + 1
        await self._recover_from_crash()
        
        # Start checkpoint flush task
        checkpoint_task = asyncio.create_task(self._batch_checkpoint_flush())
        
        logger.info(
            "biometric_bridge_started",
            consumer_group='neuros-cognitive-processor',
            max_concurrent_events=self.max_concurrent_events,
            checkpoint_interval=self.checkpoint_interval_seconds,
            thresholds=self.thresholds
        )
        
        try:
            # Main consumption loop with batch processing
            while self.running:
                # Poll for messages with retry
                records = await self._poll_with_retry(timeout_ms=1000)
                
                if records:
                    # Log consumer lag
                    await self._log_consumer_lag()
                    
                    # Process batch concurrently
                    await self._process_batch(records)
                
                # Periodic metrics logging
                if self.events_processed % 100 == 0 and self.events_processed > 0:
                    await self._log_metrics()
                
        except Exception as e:
            logger.error(
                "consumer_loop_fatal_error",
                error=str(e),
                error_type=type(e).__name__,
                events_processed=self.events_processed
            )
            raise
        finally:
            # Cancel checkpoint task
            checkpoint_task.cancel()
            try:
                await checkpoint_task
            except asyncio.CancelledError:
                pass
            
            await self._cleanup()
    
    async def _batch_checkpoint_flush(self):
        """Periodically flush pending checkpoints to reduce database load"""
        while self.running:
            try:
                await asyncio.sleep(self.checkpoint_interval_seconds)
                
                if self.pending_checkpoints:
                    logger.info(
                        "flushing_checkpoints",
                        count=len(self.pending_checkpoints)
                    )
                    
                    # Prevent queue overflow
                    if len(self.pending_checkpoints) >= self.max_pending_checkpoints:
                        checkpoint_queue_full_total.inc()
                        logger.warning(
                            "checkpoint_queue_full",
                            size=len(self.pending_checkpoints),
                            max_size=self.max_pending_checkpoints
                        )
                    
                    # Flush all pending checkpoints
                    with checkpoint_save_duration.time():
                        for session_id, state in list(self.pending_checkpoints.items()):
                            try:
                                config = {
                                    "configurable": {
                                        "thread_id": session_id,
                                        "checkpoint_ns": f"batch_{datetime.now().timestamp()}"
                                    }
                                }
                                await self.checkpointer.aput(
                                    config=config,
                                    checkpoint={"values": state}
                                )
                                # Remove from pending after successful save
                                del self.pending_checkpoints[session_id]
                            except Exception as e:
                                logger.error(
                                    "checkpoint_flush_failed",
                                    session_id=session_id,
                                    error=str(e)
                                )
                    
                    self.last_checkpoint_flush = datetime.now()
                    
            except asyncio.CancelledError:
                # Clean shutdown
                logger.info("checkpoint_flush_task_cancelled")
                break
            except Exception as e:
                logger.error(
                    "checkpoint_flush_error",
                    error=str(e)
                )
    
    async def _recover_from_crash(self):
        """Recover from crash by seeking to last committed offset + 1"""
        try:
            # Get committed offsets for all partitions
            partitions = self.consumer.assignment()
            if not partitions:
                self.consumer.subscribe(['biometric-events'])
                # Wait for assignment
                await asyncio.sleep(1)
                partitions = self.consumer.assignment()
            
            for partition in partitions:
                committed = self.consumer.committed(partition)
                if committed is not None:
                    # Seek to next message after last committed
                    seek_offset = committed + 1
                    self.consumer.seek(partition, seek_offset)
                    logger.info(
                        "crash_recovery",
                        partition=partition.partition,
                        committed_offset=committed,
                        seek_offset=seek_offset
                    )
                    
        except Exception as e:
            logger.error(
                "crash_recovery_failed",
                error=str(e),
                action="starting_from_latest"
            )
    
    async def _log_consumer_lag(self):
        """Log Kafka consumer lag for monitoring"""
        try:
            lag_total = 0
            
            # Get end offsets for all partitions (kafka-python API)
            partitions = self.consumer.assignment()
            if partitions:
                # Get current positions
                positions = {}
                for partition in partitions:
                    positions[partition] = self.consumer.position(partition)
                
                # Get end offsets (highwater marks)
                end_offsets = await self._get_end_offsets_async(partitions)
                
                # Calculate lag
                for partition, end_offset in end_offsets.items():
                    current_position = positions.get(partition, 0)
                    if end_offset and current_position:
                        lag = end_offset - current_position
                        lag_total += lag
            
            kafka_consumer_lag.set(lag_total)
            
            if lag_total > 1000:
                logger.warning(
                    "high_consumer_lag",
                    lag_messages=lag_total,
                    threshold=1000
                )
                
        except Exception as e:
            logger.error("lag_calculation_failed", error=str(e))
    
    async def _get_end_offsets_async(self, partitions):
        """Get end offsets in thread to avoid blocking"""
        loop = asyncio.get_running_loop()
        
        def _get_offsets():
            with self.consumer_lock:
                if self.consumer:
                    return self.consumer.end_offsets(list(partitions))
                return {}
        
        return await loop.run_in_executor(self.executor, _get_offsets)
    
    async def _process_batch(self, records):
        """Process a batch of Kafka records concurrently"""
        tasks = []
        
        for topic_partition, messages in records.items():
            for message in messages:
                # Create task for each message
                task = self._process_message_with_semaphore(message)
                tasks.append(task)
        
        # Process all messages in batch concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results and commit offsets
        all_successful = all(
            result is True or not isinstance(result, Exception) 
            for result in results
        )
        
        if all_successful:
            # Commit offsets only if all messages processed successfully
            # Use thread executor for commit_async
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, self.consumer.commit_async)
            kafka_messages_processed.labels(status="success").inc(len(tasks))
        else:
            # Log failures but continue processing
            failures = sum(1 for r in results if isinstance(r, Exception))
            kafka_messages_processed.labels(status="failed").inc(failures)
            kafka_messages_processed.labels(status="success").inc(len(tasks) - failures)
            
            logger.error(
                "batch_processing_failures",
                total_messages=len(tasks),
                failures=failures,
                success_rate=(len(tasks) - failures) / len(tasks) if tasks else 0
            )
    
    async def _process_message_with_semaphore(self, message):
        """Process single message with concurrency control"""
        async with self.processing_semaphore:
            try:
                biometric_data = message.value
                
                # Deserialize biometric event
                if isinstance(biometric_data, dict):
                    event = BiometricEvent(**biometric_data)  # Use proper deserialization
                else:
                    event = biometric_data
                
                # Process the event
                await self._process_biometric_event(event)
                
                self.events_processed += 1
                return True
                
            except Exception as e:
                logger.error(
                    "message_processing_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    topic=message.topic,
                    partition=message.partition,
                    offset=message.offset
                )
                self.errors_count += 1
                
                # Store failed message for retry
                await self._store_failed_message(message)
                
                # Return exception to indicate failure
                return e
    
    async def _process_biometric_event(self, event: BiometricEvent):
        """
        Process biometric event and trigger mode switches if needed
        
        This is where the MAGIC happens!
        """
        logger.info(
            "processing_biometric_event",
            device_type=event.device_type.value,
            user_id=event.user_id,
            reading_count=len(event.readings)
        )
        
        # Get or create session for user
        session_id = await self._get_or_create_session(event.user_id)
        
        # Load checkpoint state
        checkpoint = await self.checkpointer.aget({"configurable": {"thread_id": session_id}})
        
        # Extract current state or create new
        if checkpoint and checkpoint.get("values"):
            current_state = checkpoint["values"]
        else:
            current_state = self._create_initial_state(event.user_id, session_id)
        
        # Calculate biometric changes
        biometric_analysis = await self._analyze_biometrics(event, current_state)
        
        # Determine if mode switch is needed
        mode_decision = await self._determine_mode_switch(biometric_analysis, current_state)
        
        if mode_decision["switch_needed"]:
            # Trigger mode switch!
            await self._trigger_mode_switch(
                user_id=event.user_id,
                session_id=session_id,
                new_mode=mode_decision["new_mode"],
                reason=mode_decision["reason"],
                confidence=mode_decision["confidence"],
                biometric_event=event,
                current_state=current_state
            )
            
            self.mode_switches += 1
            
            # Track in Prometheus
            mode_switches_total.labels(
                from_mode=current_state["current_mode"].value,
                to_mode=mode_decision["new_mode"].value,
                reason=mode_decision["reason"][:50]  # Truncate reason for label
            ).inc()
        else:
            # Update biometrics without mode switch
            await self._update_biometrics_only(
                user_id=event.user_id,
                session_id=session_id,
                biometric_event=event,
                current_state=current_state
            )
    
    async def _get_or_create_session(self, user_id: str) -> str:
        """Get existing session or create new one with proper isolation"""
        if user_id in self.active_sessions:
            return self.active_sessions[user_id]
        
        # Create new session
        session_id = f"{user_id}:{datetime.now().isoformat()}"
        self.active_sessions[user_id] = session_id
        
        # Initialize session in database
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_sessions (user_id, session_id, created_at, last_active)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) 
                DO UPDATE SET session_id = $2, last_active = $4
            """, user_id, session_id, datetime.now(), datetime.now())
        
        return session_id
    
    def _create_initial_state(self, user_id: str, session_id: str) -> NEUROSState:
        """Create initial state for new user session"""
        return NEUROSState(
            messages=[],
            current_mode=CognitiveMode.PATTERN,
            previous_mode=None,
            mode_confidence=0.5,
            mode_history=[],
            latest_biometric_event=None,
            hrv_current=None,
            hrv_baseline=None,
            hrv_drop=None,
            heart_rate=None,
            stress_level=None,
            recovery_score=None,
            user_id=user_id,
            session_id=session_id,
            last_biometric_trigger=None,
            trigger_timestamp=None,
            active_hypothesis=None,
            pattern_detections=[],
            checkpoint_id=None,
            last_checkpoint=None,
            checkpoint_version=1,
            error_count=0,
            last_error=None,
            processing_lock=False,
            parallel_tasks=[]
        )
    
    async def _analyze_biometrics(self, event: BiometricEvent, 
                                  current_state: NEUROSState) -> Dict[str, Any]:
        """
        Comprehensive biometric analysis with baseline comparison
        """
        analysis = {
            "timestamp": event.timestamp,
            "device": event.device_type.value,
            "metrics": {}
        }
        
        # Get user's baseline from database
        baseline = await self._get_user_baseline(event.user_id)
        
        # Analyze HRV if available
        if event.hrv is not None:
            hrv_baseline = baseline.get("hrv", 60)
            hrv_drop = max(0, hrv_baseline - event.hrv)
            hrv_drop_percentage = (hrv_drop / hrv_baseline) * 100 if hrv_baseline > 0 else 0
            
            analysis["metrics"]["hrv"] = {
                "current": event.hrv,
                "baseline": hrv_baseline,
                "drop": hrv_drop,
                "drop_percentage": hrv_drop_percentage,
                "significant": hrv_drop > 20 or hrv_drop_percentage > 30
            }
        
        # Analyze heart rate
        if event.heart_rate is not None:
            hr_baseline = baseline.get("heart_rate", 70)
            hr_elevation = max(0, event.heart_rate - hr_baseline)
            
            analysis["metrics"]["heart_rate"] = {
                "current": event.heart_rate,
                "baseline": hr_baseline,
                "elevation": hr_elevation,
                "elevated": event.heart_rate > 100,
                "significant": hr_elevation > 20
            }
        
        # Analyze stress level
        if event.stress_level is not None:
            analysis["metrics"]["stress"] = {
                "level": event.stress_level,
                "high": event.stress_level > 0.7,
                "critical": event.stress_level > 0.85
            }
        else:
            # Calculate stress from other metrics
            calculated_stress = self._calculate_stress_level(analysis)
            analysis["metrics"]["stress"] = {
                "level": calculated_stress,
                "high": calculated_stress > 0.7,
                "critical": calculated_stress > 0.85,
                "calculated": True
            }
        
        # Check for patterns
        patterns = await self._detect_patterns(event.user_id, analysis)
        if patterns:
            analysis["patterns"] = patterns
        
        # Check for anomalies
        anomalies = self._detect_anomalies(analysis, baseline)
        if anomalies:
            analysis["anomalies"] = anomalies
        
        return analysis
    
    async def _get_user_baseline(self, user_id: str) -> Dict[str, float]:
        """
        Get user's biometric baselines from database
        
        Uses 7-day rolling average for accuracy
        """
        try:
            async with self.postgres_pool.acquire() as conn:
                # Get average metrics from last 7 days
                result = await conn.fetchrow("""
                    SELECT 
                        AVG((event_data->'readings'->0->>'value')::float) 
                            FILTER (WHERE event_data->'readings'->0->>'metric' = 'hrv') as hrv_baseline,
                        AVG((event_data->'readings'->0->>'value')::float) 
                            FILTER (WHERE event_data->'readings'->0->>'metric' = 'heart_rate') as hr_baseline,
                        AVG((event_data->'readings'->0->>'value')::float) 
                            FILTER (WHERE event_data->'readings'->0->>'metric' = 'recovery_score') as recovery_baseline
                    FROM biometric_events
                    WHERE user_id = $1 
                    AND timestamp > NOW() - INTERVAL '7 days'
                """, user_id)
                
                if result:
                    return {
                        "hrv": result["hrv_baseline"] or self.baselines["hrv_default"],
                        "heart_rate": result["hr_baseline"] or self.baselines["heart_rate_default"],
                        "recovery_score": result["recovery_baseline"] or self.baselines["recovery_score_default"]
                    }
                
        except Exception as e:
            logger.error(f"Failed to get baseline: {e}")
        
        # Return defaults if no data
        return self.baselines
    
    def _calculate_stress_level(self, analysis: Dict[str, Any]) -> float:
        """Calculate stress level from available biometrics"""
        stress = 0.0
        factors = 0
        
        # HRV contribution
        if "hrv" in analysis["metrics"]:
            hrv_data = analysis["metrics"]["hrv"]
            if hrv_data["significant"]:
                stress += min(0.5, hrv_data["drop_percentage"] / 100)
                factors += 1
        
        # Heart rate contribution
        if "heart_rate" in analysis["metrics"]:
            hr_data = analysis["metrics"]["heart_rate"]
            if hr_data["elevated"]:
                stress += min(0.3, hr_data["elevation"] / 50)
                factors += 1
            elif hr_data["current"] > 90:
                stress += 0.2
                factors += 1
        
        # Recovery score contribution (if available)
        if "recovery" in analysis["metrics"]:
            recovery = analysis["metrics"]["recovery"]["current"]
            if recovery < 40:
                stress += 0.3
                factors += 1
            elif recovery < 60:
                stress += 0.1
                factors += 1
        
        # Average the stress factors
        if factors > 0:
            stress = stress / factors
        
        return min(1.0, stress * 1.5)  # Scale up slightly
    
    async def _detect_patterns(self, user_id: str, 
                               analysis: Dict[str, Any]) -> List[str]:
        """
        Detect recurring patterns in biometric data
        
        Looks for time-based, day-based, and trigger-based patterns
        """
        patterns = []
        current_hour = analysis["timestamp"].hour
        current_day = analysis["timestamp"].weekday()
        
        try:
            async with self.postgres_pool.acquire() as conn:
                # Check hourly pattern
                hourly_result = await conn.fetchrow("""
                    SELECT COUNT(*) as occurrences,
                           AVG((event_data->'readings'->0->>'value')::float) as avg_value
                    FROM biometric_events
                    WHERE user_id = $1
                    AND EXTRACT(HOUR FROM timestamp) = $2
                    AND timestamp > NOW() - INTERVAL '30 days'
                    AND event_data->'readings'->0->>'metric' = 'hrv'
                    AND (event_data->'readings'->0->>'value')::float < $3
                """, user_id, current_hour, analysis.get("metrics", {}).get("hrv", {}).get("baseline", 60) - 15)
                
                if hourly_result and hourly_result["occurrences"] >= 5:
                    patterns.append(f"recurring_stress_hour_{current_hour}")
                
                # Check weekly pattern
                weekly_result = await conn.fetchrow("""
                    SELECT COUNT(*) as occurrences
                    FROM biometric_events
                    WHERE user_id = $1
                    AND EXTRACT(DOW FROM timestamp) = $2
                    AND timestamp > NOW() - INTERVAL '8 weeks'
                    AND (event_data->>'recovery_score')::float < 50
                """, user_id, current_day)
                
                if weekly_result and weekly_result["occurrences"] >= 3:
                    day_names = ["sunday", "monday", "tuesday", "wednesday", 
                                 "thursday", "friday", "saturday"]
                    patterns.append(f"low_recovery_{day_names[current_day]}")
                
                # Check post-workout pattern
                # (This would require workout data integration)
                
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
        
        return patterns
    
    def _detect_anomalies(self, analysis: Dict[str, Any], 
                          baseline: Dict[str, float]) -> List[str]:
        """Detect anomalous readings that don't fit normal patterns"""
        anomalies = []
        
        # Check for physiologically unusual combinations
        metrics = analysis.get("metrics", {})
        
        # High HRV + High HR is unusual
        if ("hrv" in metrics and "heart_rate" in metrics):
            if (metrics["hrv"]["current"] > baseline["hrv"] * 1.5 and 
                metrics["heart_rate"]["current"] > 90):
                anomalies.append("high_hrv_high_hr")
        
        # Very low HRV + Low HR is concerning
        if ("hrv" in metrics and "heart_rate" in metrics):
            if (metrics["hrv"]["current"] < 20 and 
                metrics["heart_rate"]["current"] < 50):
                anomalies.append("low_hrv_low_hr")
        
        # Extreme deviations
        if "hrv" in metrics:
            if metrics["hrv"]["drop_percentage"] > 50:
                anomalies.append("extreme_hrv_drop")
        
        if "heart_rate" in metrics:
            if metrics["heart_rate"]["elevation"] > 40:
                anomalies.append("extreme_hr_elevation")
        
        return anomalies
    
    async def _determine_mode_switch(self, analysis: Dict[str, Any], 
                                     current_state: NEUROSState) -> Dict[str, Any]:
        """
        Determine if cognitive mode switch is needed based on biometric analysis
        using configuration-driven thresholds
        """
        decision = {
            "switch_needed": False,
            "new_mode": current_state["current_mode"],
            "reason": "",
            "confidence": 0.0,
            "borderline_trigger": None  # Track borderline cases
        }
        
        metrics = analysis.get("metrics", {})
        patterns = analysis.get("patterns", [])
        anomalies = analysis.get("anomalies", [])
        
        # Calculate confidence BEFORE deciding on switch
        potential_decisions = []
        
        # Check REFLEX MODE triggers
        reflex_triggered, reflex_reason = self._check_reflex_triggers(metrics, anomalies)
        if reflex_triggered:
            reflex_confidence = self._calculate_reflex_confidence(metrics)
            potential_decisions.append({
                "mode": CognitiveMode.REFLEX,
                "reason": reflex_reason,
                "confidence": reflex_confidence,
                "priority": 1
            })
        elif self._is_borderline_reflex(metrics):
            decision["borderline_trigger"] = {
                "mode": "reflex",
                "metrics": {
                    "hrv_drop": metrics.get("hrv", {}).get("drop", 0),
                    "heart_rate": metrics.get("heart_rate", {}).get("current", 0),
                    "stress_level": metrics.get("stress", {}).get("level", 0)
                },
                "reason": "Metrics approaching reflex thresholds"
            }
        
        # Check GUARDIAN MODE triggers
        if self._should_trigger_guardian(metrics, current_state):
            guardian_confidence = self._calculate_guardian_confidence(metrics)
            guardian_reason = (f"Low recovery state: {metrics['recovery']['current']:.0f}%" 
                             if "recovery" in metrics else "Chronic depletion indicators detected")
            potential_decisions.append({
                "mode": CognitiveMode.GUARDIAN,
                "reason": guardian_reason,
                "confidence": guardian_confidence,
                "priority": 2
            })
        
        # Check PATTERN MODE triggers
        if patterns and current_state["current_mode"] != CognitiveMode.PATTERN:
            potential_decisions.append({
                "mode": CognitiveMode.PATTERN,
                "reason": f"Recurring pattern detected: {patterns[0]}",
                "confidence": 0.7,
                "priority": 3
            })
        
        # Check HYPOTHESIS MODE triggers
        if anomalies and current_state["current_mode"] != CognitiveMode.HYPOTHESIS:
            potential_decisions.append({
                "mode": CognitiveMode.HYPOTHESIS,
                "reason": f"Anomalous readings detected: {anomalies[0]}",
                "confidence": 0.6,
                "priority": 4
            })
        
        # Check return to baseline
        if (current_state["current_mode"] != CognitiveMode.PATTERN and
            self._should_return_to_baseline(metrics, current_state)):
            potential_decisions.append({
                "mode": CognitiveMode.PATTERN,
                "reason": "Biometrics returned to normal range",
                "confidence": 0.8,
                "priority": 5
            })
        
        # Apply cooldown to ALL potential decisions
        last_switch = current_state.get("trigger_timestamp")
        if last_switch:
            time_since_switch = (datetime.now() - datetime.fromisoformat(last_switch)).seconds
            cooldown = self.thresholds.get("mode_switch_cooldown_seconds", 300)
            
            if time_since_switch < cooldown:
                # Apply cooldown penalty to all decisions
                for pd in potential_decisions:
                    original_confidence = pd["confidence"]
                    pd["confidence"] *= 0.7
                    pd["cooldown_applied"] = True
                    pd["original_confidence"] = original_confidence
        
        # Select highest priority decision with sufficient confidence
        for pd in sorted(potential_decisions, key=lambda x: x["priority"]):
            if pd["confidence"] >= 0.5:
                decision["switch_needed"] = True
                decision["new_mode"] = pd["mode"]
                decision["reason"] = pd["reason"]
                decision["confidence"] = pd["confidence"]
                
                if pd.get("cooldown_applied"):
                    logger.info(
                        "mode_switch_with_cooldown",
                        time_since_last=time_since_switch,
                        original_confidence=pd.get("original_confidence", pd["confidence"] / 0.7),
                        reduced_confidence=pd["confidence"]
                    )
                break
        
        # Log borderline triggers that didn't fire
        if decision.get("borderline_trigger") and not decision["switch_needed"]:
            logger.info(
                "borderline_trigger_not_fired",
                **decision["borderline_trigger"]
            )
        
        # Log all suppressed decisions
        if not decision["switch_needed"] and potential_decisions:
            logger.info(
                "all_mode_switches_suppressed",
                potential_switches=[{
                    "mode": pd["mode"].value,
                    "confidence": pd["confidence"],
                    "reason": pd["reason"][:50]  # Truncate for logging
                } for pd in potential_decisions]
            )
        
        return decision
    
    def _check_reflex_triggers(self, metrics: Dict[str, Any], 
                               anomalies: List[str]) -> tuple[bool, str]:
        """Check reflex triggers using configuration thresholds"""
        # HRV drop check
        if "hrv" in metrics:
            hrv_data = metrics["hrv"]
            if (hrv_data.get("drop", 0) > self.thresholds["hrv_drop_ms"] or 
                hrv_data.get("drop_percentage", 0) > self.thresholds["hrv_drop_percentage"]):
                reason = f"Acute stress detected: HRV dropped {hrv_data['drop']:.1f}ms ({hrv_data['drop_percentage']:.0f}%)"
                return True, reason
        
        # Heart rate check
        if "heart_rate" in metrics:
            hr_data = metrics["heart_rate"]
            if hr_data["current"] > self.thresholds["heart_rate_elevated"]:
                reason = f"Elevated heart rate: {hr_data['current']}bpm"
                return True, reason
        
        # Stress level check
        if "stress" in metrics:
            stress_data = metrics["stress"]
            if stress_data["level"] > self.thresholds["stress_level_critical"]:
                reason = f"Critical stress level: {stress_data['level']:.1%}"
                return True, reason
        
        # Extreme anomalies
        if any(a in anomalies for a in ["extreme_hrv_drop", "extreme_hr_elevation"]):
            return True, "Multiple stress indicators detected"
        
        return False, ""
    
    def _is_borderline_reflex(self, metrics: Dict[str, Any]) -> bool:
        """Check if metrics are close to reflex thresholds"""
        borderline_factors = 0
        
        # Check if within 10% of thresholds
        if "hrv" in metrics:
            hrv_drop = metrics["hrv"]["drop"]
            if hrv_drop > self.thresholds["hrv_drop_ms"] * 0.9:
                borderline_factors += 1
        
        if "heart_rate" in metrics:
            hr = metrics["heart_rate"]["current"]
            if hr > self.thresholds["heart_rate_elevated"] * 0.9:
                borderline_factors += 1
        
        if "stress" in metrics:
            stress = metrics["stress"]["level"]
            if stress > self.thresholds["stress_level_critical"] * 0.9:
                borderline_factors += 1
        
        return borderline_factors >= 2
    
    def _should_trigger_guardian(self, metrics: Dict[str, Any], 
                                 current_state: NEUROSState) -> bool:
        """Determine if guardian mode should be triggered"""
        # Recovery score < 40
        if "recovery" in metrics:
            if metrics["recovery"]["current"] < self.thresholds["recovery_score_low"]:
                return True
        
        # Multiple low indicators
        low_indicators = 0
        
        if "hrv" in metrics and metrics["hrv"]["current"] < 30:
            low_indicators += 1
        
        if "heart_rate" in metrics and metrics["heart_rate"]["current"] > 80:
            low_indicators += 1
        
        if "stress" in metrics and metrics["stress"]["level"] > self.thresholds["stress_level_high"]:
            low_indicators += 1
        
        return low_indicators >= 2
    
    def _calculate_reflex_confidence(self, metrics: Dict[str, Any]) -> float:
        """Calculate confidence for reflex mode trigger"""
        confidence = 0.0
        factors = 0
        
        # HRV contribution
        if "hrv" in metrics and metrics["hrv"]["significant"]:
            # Scale confidence based on severity
            hrv_confidence = min(1.0, metrics["hrv"]["drop"] / 30)
            confidence += hrv_confidence
            factors += 1
        
        # Heart rate contribution
        if "heart_rate" in metrics and metrics["heart_rate"]["elevated"]:
            hr_confidence = min(1.0, (metrics["heart_rate"]["current"] - 90) / 30)
            confidence += hr_confidence
            factors += 1
        
        # Stress level contribution
        if "stress" in metrics and metrics["stress"]["high"]:
            confidence += metrics["stress"]["level"]
            factors += 1
        
        if factors > 0:
            confidence = confidence / factors
        
        return max(0.5, min(1.0, confidence))
    
    def _calculate_guardian_confidence(self, metrics: Dict[str, Any]) -> float:
        """Calculate confidence for guardian mode trigger"""
        if "recovery" in metrics:
            # Inverse of recovery score
            return 1.0 - (metrics["recovery"]["current"] / 100)
        
        # Based on other indicators
        confidence = 0.0
        
        if "hrv" in metrics and metrics["hrv"]["current"] < 40:
            confidence += 0.3
        
        if "stress" in metrics:
            confidence += metrics["stress"]["level"] * 0.5
        
        return min(0.9, confidence)
    
    def _should_return_to_baseline(self, metrics: Dict[str, Any], 
                                    current_state: NEUROSState) -> bool:
        """Determine if we should return to baseline pattern mode"""
        # Check if all metrics are within normal range
        normal_indicators = 0
        total_indicators = 0
        
        if "hrv" in metrics:
            total_indicators += 1
            if not metrics["hrv"]["significant"]:
                normal_indicators += 1
        
        if "heart_rate" in metrics:
            total_indicators += 1
            if not metrics["heart_rate"]["elevated"]:
                normal_indicators += 1
        
        if "stress" in metrics:
            total_indicators += 1
            if not metrics["stress"]["high"]:
                normal_indicators += 1
        
        if "recovery" in metrics:
            total_indicators += 1
            if metrics["recovery"]["current"] > self.thresholds["recovery_score_moderate"]:
                normal_indicators += 1
        
        # Return to baseline if 80% of indicators are normal
        if total_indicators > 0:
            return (normal_indicators / total_indicators) >= 0.8
        
        return False
    
    async def _trigger_mode_switch(self, user_id: str, session_id: str,
                                   new_mode: CognitiveMode, reason: str,
                                   confidence: float, biometric_event: BiometricEvent,
                                   current_state: NEUROSState):
        """
        Execute cognitive mode transition with full state management
        
        This is the MOMENT OF MAGIC where biometrics change AI behavior!
        """
        logger.warning(f"🧠 MODE SWITCH for {user_id}: {current_state['current_mode']} → {new_mode} - {reason} (confidence: {confidence:.1%})")
        
        try:
            # Prepare state update
            state_update = {
                # Add system message about the mode switch
                "messages": [
                    SystemMessage(content=f"BIOMETRIC_TRIGGER: {reason}"),
                    SystemMessage(content=f"COGNITIVE_MODE_SWITCH: {new_mode.value}")
                ],
                
                # Update mode information
                "current_mode": new_mode,
                "previous_mode": current_state["current_mode"],
                "mode_confidence": confidence,
                
                # Update biometric data
                "latest_biometric_event": biometric_event.to_dict(),
                "hrv_current": biometric_event.hrv,
                "heart_rate": biometric_event.heart_rate,
                "stress_level": biometric_event.stress_level,
                
                # Update trigger information
                "last_biometric_trigger": reason,
                "trigger_timestamp": datetime.now().isoformat(),
                
                # Update mode history
                "mode_history": current_state.get("mode_history", []) + [{
                    "timestamp": datetime.now().isoformat(),
                    "from_mode": current_state["current_mode"].value,
                    "to_mode": new_mode.value,
                    "reason": reason,
                    "confidence": confidence,
                    "biometric_snapshot": {
                        "hrv": biometric_event.hrv,
                        "heart_rate": biometric_event.heart_rate,
                        "stress_level": biometric_event.stress_level
                    }
                }]
            }
            
            # Limit mode history size
            if len(state_update["mode_history"]) > self.max_mode_history:
                state_update["mode_history"] = state_update["mode_history"][-self.max_mode_history:]
            
            # Update checkpoint version
            state_update["checkpoint_version"] = current_state.get("checkpoint_version", 0) + 1
            state_update["last_checkpoint"] = datetime.now().isoformat()
            
            # Merge with current state
            updated_state = {**current_state, **state_update}
            
            # Add appropriate user message based on mode
            user_message = self._generate_mode_message(new_mode, reason, confidence)
            updated_state["messages"].append(HumanMessage(content=user_message))
            
            # Invoke graph with updated state
            config = {
                "configurable": {
                    "thread_id": session_id,
                    "checkpoint_ns": f"biometric_trigger_{datetime.now().timestamp()}"
                }
            }
            
            # Run the graph with new state
            result = await self.graph.ainvoke(
                updated_state,
                config=config
            )
            
            # Save checkpoint
            await self.checkpointer.aput(
                config=config,
                checkpoint={
                    "values": result,
                    "metadata": {
                        "mode": new_mode.value,
                        "trigger_reason": reason,
                        "confidence": confidence,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            )
            
            # Update session tracking
            await self._update_session_state(user_id, session_id, new_mode, reason)
            
            # Publish mode switch event
            self.producer.send('neuros-mode-switches', {
                "user_id": user_id,
                "session_id": session_id,
                "previous_mode": current_state["current_mode"].value,
                "new_mode": new_mode.value,
                "reason": reason,
                "confidence": confidence,
                "biometric_snapshot": {
                    "hrv": biometric_event.hrv,
                    "heart_rate": biometric_event.heart_rate,
                    "stress_level": biometric_event.stress_level,
                    "device": biometric_event.device_type.value
                },
                "timestamp": datetime.now().isoformat()
            })
            
            # Send real-time update via WebSocket (if configured)
            await self._send_websocket_update(user_id, {
                "type": "mode_switch",
                "mode": new_mode.value,
                "reason": reason,
                "confidence": confidence
            })
            
            logger.info(f"✅ Mode switch completed successfully for {user_id}")
            
        except Exception as e:
            logger.error(f"Mode switch failed: {e}")
            self.errors_count += 1
            
            # Store failure for analysis
            await self._store_mode_switch_failure(
                user_id, new_mode, reason, confidence, 
                biometric_event, str(e)
            )
    
    def _generate_mode_message(self, mode: CognitiveMode, reason: str, 
                               confidence: float) -> str:
        """Generate appropriate message for mode transition"""
        if mode == CognitiveMode.REFLEX:
            if "HRV dropped" in reason:
                return "I'm noticing some stress signals in my body. My HRV just dropped significantly."
            elif "heart rate" in reason:
                return "My heart is racing. Something feels urgent right now."
            else:
                return "I'm feeling overwhelmed. I need to reset."
        
        elif mode == CognitiveMode.GUARDIAN:
            return "I'm running on low reserves. My body needs recovery and protection right now."
        
        elif mode == CognitiveMode.PATTERN:
            if "returned to normal" in reason:
                return "I'm feeling more balanced now. Things are stabilizing."
            else:
                return "I'm noticing a familiar pattern here. Let me analyze what's happening."
        
        elif mode == CognitiveMode.HYPOTHESIS:
            return "Something unusual is happening with my biometrics. I need to explore this carefully."
        
        return f"My cognitive state is shifting based on: {reason}"
    
    async def _update_biometrics_only(self, user_id: str, session_id: str,
                                      biometric_event: BiometricEvent,
                                      current_state: NEUROSState):
        """Update biometric data without triggering mode switch"""
        try:
            # Prepare minimal state update
            state_update = {
                "latest_biometric_event": biometric_event.to_dict(),
                "hrv_current": biometric_event.hrv,
                "heart_rate": biometric_event.heart_rate,
                "stress_level": biometric_event.stress_level,
                "checkpoint_version": current_state.get("checkpoint_version", 0) + 1,
                "last_checkpoint": datetime.now().isoformat()
            }
            
            # Merge with current state
            updated_state = {**current_state, **state_update}
            
            # Batch checkpoint updates to reduce database load
            self.pending_checkpoints[session_id] = updated_state
            
            # Check if significant enough to force immediate save
            if self._is_significant_change(current_state, updated_state):
                config = {
                    "configurable": {
                        "thread_id": session_id,
                        "checkpoint_ns": f"biometric_update_{datetime.now().timestamp()}"
                    }
                }
                
                await self.checkpointer.aput(
                    config=config,
                    checkpoint={
                        "values": updated_state,
                        "metadata": {
                            "type": "biometric_update",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
                
                # Remove from pending since we saved it
                if session_id in self.pending_checkpoints:
                    del self.pending_checkpoints[session_id]
            
            # Update Redis cache for quick access
            await self._update_redis_biometrics(user_id, biometric_event)
            
        except Exception as e:
            logger.error(f"Failed to update biometrics: {e}")
    
    def _is_significant_change(self, old_state: Dict[str, Any], 
                                new_state: Dict[str, Any]) -> bool:
        """Determine if biometric change is significant enough for immediate save"""
        # Check HRV change
        old_hrv = old_state.get("hrv_current", 0)
        new_hrv = new_state.get("hrv_current", 0)
        if abs(old_hrv - new_hrv) > self.significant_change_thresholds["hrv"]:
            return True
        
        # Check heart rate change
        old_hr = old_state.get("heart_rate", 0)
        new_hr = new_state.get("heart_rate", 0)
        if abs(old_hr - new_hr) > self.significant_change_thresholds["heart_rate"]:
            return True
        
        # Check stress level change
        old_stress = old_state.get("stress_level", 0)
        new_stress = new_state.get("stress_level", 0)
        if abs(old_stress - new_stress) > self.significant_change_thresholds["stress_level"]:
            return True
        
        return False
    
    async def _update_session_state(self, user_id: str, session_id: str,
                                    mode: CognitiveMode, reason: str):
        """Update session state in database"""
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE user_sessions 
                    SET current_mode = $1, 
                        last_mode_switch = $2,
                        last_switch_reason = $3,
                        mode_switch_count = mode_switch_count + 1,
                        last_active = $4
                    WHERE user_id = $5 AND session_id = $6
                """, mode.value, datetime.now(), reason, datetime.now(), 
                    user_id, session_id)
        except Exception as e:
            logger.error(f"Failed to update session state: {e}")
    
    async def _update_redis_biometrics(self, user_id: str, 
                                       biometric_event: BiometricEvent):
        """Update Redis with latest biometric data"""
        try:
            with redis_operation_duration.labels(operation="update_biometrics").time():
                pipe = self.redis_client.pipeline()
                
                # Store latest biometrics
                key = f"user:{user_id}:biometrics:latest"
                pipe.hset(key, mapping={
                    "hrv": biometric_event.hrv or 0,
                    "heart_rate": biometric_event.heart_rate or 0,
                    "stress_level": biometric_event.stress_level or 0,
                    "device": biometric_event.device_type.value,
                    "timestamp": biometric_event.timestamp.isoformat()
                })
                
                # Set expiry
                pipe.expire(key, 3600)  # 1 hour
                
                pipe.execute()
            
        except Exception as e:
            logger.error(f"Redis update failed: {e}")
    
    async def _send_websocket_update(self, user_id: str, update: Dict[str, Any]):
        """Send real-time update via WebSocket"""
        # This would integrate with your existing WebSocket infrastructure
        # For now, just log it
        logger.info(f"WebSocket update for {user_id}: {update}")
    
    async def _store_failed_message(self, message):
        """Store failed Kafka message for retry"""
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO failed_biometric_events 
                    (topic, partition, offset, value, error, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, message.topic, message.partition, message.offset,
                    json.dumps(message.value), "Processing failed", datetime.now())
        except Exception as e:
            logger.error(f"Failed to store failed message: {e}")
    
    async def _store_mode_switch_failure(self, user_id: str, mode: CognitiveMode,
                                         reason: str, confidence: float,
                                         event: BiometricEvent, error: str):
        """Store failed mode switch for analysis"""
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO failed_mode_switches 
                    (user_id, target_mode, reason, confidence, biometric_event, error, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, user_id, mode.value, reason, confidence,
                    json.dumps(event.to_dict()), error, datetime.now())
        except Exception as e:
            logger.error(f"Failed to store mode switch failure: {e}")
    
    async def _log_metrics(self):
        """Log processing metrics periodically"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        events_per_second = self.events_processed / uptime if uptime > 0 else 0
        mode_switch_rate = self.mode_switches / self.events_processed if self.events_processed > 0 else 0
        error_rate = self.errors_count / self.events_processed if self.events_processed > 0 else 0
        
        logger.info(f"""
        📊 Biometric Bridge Metrics:
        - Events Processed: {self.events_processed:,}
        - Mode Switches: {self.mode_switches:,}
        - Errors: {self.errors_count:,}
        - Events/Second: {events_per_second:.2f}
        - Mode Switch Rate: {mode_switch_rate:.2%}
        - Error Rate: {error_rate:.2%}
        - Uptime: {uptime/3600:.1f} hours
        """)
        
        # Also publish to monitoring topic
        self.producer.send('system-metrics', {
            "service": "biometric-bridge",
            "metrics": {
                "events_processed": self.events_processed,
                "mode_switches": self.mode_switches,
                "errors": self.errors_count,
                "events_per_second": events_per_second,
                "mode_switch_rate": mode_switch_rate,
                "error_rate": error_rate,
                "uptime_hours": uptime/3600
            },
            "timestamp": datetime.now().isoformat()
        })
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status for monitoring endpoint"""
        try:
            # Check PostgreSQL checkpoint latency
            start_time = datetime.now()
            test_config = {"configurable": {"thread_id": "health_check"}}
            await self.checkpointer.aget(test_config)
            postgres_latency = (datetime.now() - start_time).total_seconds()
            
            # Check Redis connectivity
            with redis_operation_duration.labels(operation="ping").time():
                redis_ping = self.redis_client.ping()
            
            return {
                "status": "healthy",
                "postgres_checkpoint_latency_seconds": postgres_latency,
                "redis_connected": redis_ping,
                "events_processed": self.events_processed,
                "mode_switches": self.mode_switches,
                "error_rate": self.errors_count / self.events_processed if self.events_processed > 0 else 0,
                "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
                "pending_checkpoints": len(self.pending_checkpoints),
                "active_sessions": len(self.active_sessions)
            }
            
        except Exception as e:
            logger.error("health_check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _cleanup(self):
        """Enhanced cleanup with producer flush"""
        logger.info("shutdown_initiated")
        
        try:
            # Flush any pending checkpoints
            if self.pending_checkpoints:
                logger.info(f"flushing_{len(self.pending_checkpoints)}_pending_checkpoints")
                for session_id, state in self.pending_checkpoints.items():
                    try:
                        config = {
                            "configurable": {
                                "thread_id": session_id,
                                "checkpoint_ns": f"shutdown_{datetime.now().timestamp()}"
                            }
                        }
                        await self.checkpointer.aput(
                            config=config,
                            checkpoint={"values": state}
                        )
                    except Exception as e:
                        logger.error(f"Failed to save checkpoint on shutdown: {e}")
            
            # Flush producer in thread to avoid blocking with timeout
            if self.producer:
                logger.info("flushing_producer_messages")
                loop = asyncio.get_running_loop()
                try:
                    await asyncio.wait_for(
                        loop.run_in_executor(
                            self.executor,
                            self.producer.flush,
                            10  # timeout seconds for flush itself
                        ),
                        timeout=15  # total timeout including thread overhead
                    )
                except asyncio.TimeoutError:
                    logger.error("producer_flush_timeout", timeout_seconds=15)
                
            # Close Kafka connections after flush completes
            if self.consumer:
                with self.consumer_lock:
                    self.consumer.close()
            
            # Close producer after flush is done
            if self.producer:
                self.producer.close()
            
            # Shutdown thread executor
            self.executor.shutdown(wait=True)
            
            # Log final metrics
            await self._log_metrics()
            
            logger.info(
                "shutdown_complete",
                total_events_processed=self.events_processed,
                total_mode_switches=self.mode_switches,
                total_errors=self.errors_count
            )
            
        except Exception as e:
            logger.error("cleanup_error", error=str(e))
    
    async def stop(self):
        """Gracefully stop the bridge"""
        self.running = False
        await self._cleanup()

# Additional configuration file template (config/biometric_thresholds.yaml)
"""
thresholds:
  # HRV thresholds
  hrv_drop_ms: 25
  hrv_drop_percentage: 30
  
  # Heart rate thresholds  
  heart_rate_elevated: 100
  heart_rate_elevation: 20
  
  # Stress thresholds
  stress_level_high: 0.7
  stress_level_critical: 0.85
  
  # Recovery thresholds
  recovery_score_low: 40
  recovery_score_moderate: 60
  
  # Mode switching
  mode_switch_cooldown_seconds: 300
  
baselines:
  hrv_default: 60
  heart_rate_default: 70
  recovery_score_default: 75
  
# Alert thresholds for monitoring
alerts:
  error_rate_threshold: 0.1  # 10% error rate
  consumer_lag_threshold: 1000
  checkpoint_latency_threshold: 5.0  # seconds
"""