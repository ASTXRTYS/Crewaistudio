# =============================================================================
# APPLE HEALTHKIT HANDLER WITH ENHANCED ERROR HANDLING
# =============================================================================

import structlog
from prometheus_client import Counter, Histogram, Gauge
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from kafka import KafkaProducer

# Import types from the types module
from .types import BiometricReading, BiometricEvent, WearableType

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