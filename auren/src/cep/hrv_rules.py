"""
HRV Complex Event Processing Rules for AUREN
Detects significant HRV drops that require Neuroscientist intervention

This module implements real-time pattern detection on biometric data streams
to trigger proactive health interventions.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import deque
import statistics

from src.database.connection import DatabaseConnection
from src.infrastructure.kafka.producer import EventProducer
from src.infrastructure.kafka.consumer import EventConsumer
from src.auren.monitoring.decorators import track_tokens
from src.auren.monitoring.otel_config import otel_trace

logger = logging.getLogger(__name__)


@dataclass
class BiometricEvent:
    """Represents a biometric data event from the stream"""
    user_id: str
    metric_type: str
    value: float
    timestamp: datetime
    device_source: str
    quality_score: float
    metadata: Dict[str, Any]


@dataclass
class HRVTrigger:
    """Represents an HRV anomaly that requires intervention"""
    user_id: str
    trigger_type: str
    severity: float  # 0.0 to 1.0
    current_value: float
    baseline_value: float
    percentage_drop: float
    timestamp: datetime
    recommendation: str
    context: Dict[str, Any]


class HRVRuleEngine:
    """
    Complex Event Processing engine for HRV monitoring
    
    This engine processes real-time biometric events and detects patterns
    that indicate the need for intervention. It maintains sliding windows
    of data and applies sophisticated rules to identify anomalies.
    """
    
    def __init__(self, window_size_minutes: int = 60):
        """
        Initialize the HRV rule engine
        
        Args:
            window_size_minutes: Size of the sliding window for analysis
        """
        self.window_size = timedelta(minutes=window_size_minutes)
        self.user_windows: Dict[str, deque] = {}  # User-specific event windows
        self.user_baselines: Dict[str, Dict[str, float]] = {}  # Cached baselines
        self.baseline_refresh_interval = timedelta(hours=6)
        self.last_baseline_refresh: Dict[str, datetime] = {}
        
        # Thresholds for different severity levels
        self.thresholds = {
            'critical': {
                'percentage_drop': 25,
                'absolute_drop': 15,
                'severity': 0.9
            },
            'moderate': {
                'percentage_drop': 20,
                'absolute_drop': 10,
                'severity': 0.6
            },
            'mild': {
                'percentage_drop': 15,
                'absolute_drop': 7,
                'severity': 0.3
            }
        }
    
    @otel_trace(operation_name="cep.process_biometric_event")
    async def process_event(self, event: BiometricEvent) -> Optional[HRVTrigger]:
        """
        Process a single biometric event and check for trigger conditions
        
        Args:
            event: The biometric event to process
            
        Returns:
            HRVTrigger if a significant anomaly is detected, None otherwise
        """
        # Only process HRV events
        if event.metric_type != 'hrv':
            return None
        
        # Initialize user window if needed
        if event.user_id not in self.user_windows:
            self.user_windows[event.user_id] = deque()
        
        # Add event to user's window
        window = self.user_windows[event.user_id]
        window.append(event)
        
        # Remove old events outside the window
        cutoff_time = datetime.utcnow() - self.window_size
        while window and window[0].timestamp < cutoff_time:
            window.popleft()
        
        # Check if we need to refresh baseline
        await self._refresh_baseline_if_needed(event.user_id)
        
        # Analyze current state
        trigger = await self._analyze_hrv_state(event.user_id, event)
        
        return trigger
    
    async def _refresh_baseline_if_needed(self, user_id: str):
        """
        Refresh user's baseline if it's stale or missing
        
        Baselines are refreshed every 6 hours to adapt to changing
        user patterns while maintaining stability.
        """
        needs_refresh = (
            user_id not in self.user_baselines or
            user_id not in self.last_baseline_refresh or
            datetime.utcnow() - self.last_baseline_refresh.get(user_id, datetime.min) > self.baseline_refresh_interval
        )
        
        if needs_refresh:
            try:
                baseline_data = await self._fetch_user_baseline(user_id)
                self.user_baselines[user_id] = baseline_data
                self.last_baseline_refresh[user_id] = datetime.utcnow()
                logger.info(f"Refreshed baseline for user {user_id}: {baseline_data}")
            except Exception as e:
                logger.error(f"Error refreshing baseline for {user_id}: {e}")
    
    async def _fetch_user_baseline(self, user_id: str) -> Dict[str, float]:
        """
        Fetch user's HRV baseline from the database
        
        Returns both the baseline value and standard deviation for
        more sophisticated anomaly detection.
        """
        query = """
            SELECT 
                baseline_value,
                stddev_value,
                sample_count
            FROM biometric_baselines
            WHERE user_id = $1 AND metric_type = 'hrv'
        """
        
        result = await DatabaseConnection.fetchrow(query, user_id)
        
        if result:
            return {
                'baseline': float(result['baseline_value']),
                'stddev': float(result['stddev_value']),
                'sample_count': int(result['sample_count'])
            }
        else:
            # Return population defaults if no baseline exists
            return {
                'baseline': 60.0,
                'stddev': 10.0,
                'sample_count': 0
            }
    
    async def _analyze_hrv_state(
        self,
        user_id: str,
        current_event: BiometricEvent
    ) -> Optional[HRVTrigger]:
        """
        Analyze current HRV state against baseline and recent history
        
        This method implements the core logic for detecting significant
        HRV drops that warrant intervention.
        """
        baseline_data = self.user_baselines.get(user_id, {})
        baseline_value = baseline_data.get('baseline', 60.0)
        stddev = baseline_data.get('stddev', 10.0)
        
        # Calculate percentage and absolute drops
        current_value = current_event.value
        percentage_drop = ((baseline_value - current_value) / baseline_value) * 100
        absolute_drop = baseline_value - current_value
        
        # Check if this is just normal variation
        if absolute_drop < stddev:  # Within 1 standard deviation
            return None
        
        # Determine severity level
        severity = None
        trigger_type = None
        recommendation = None
        
        for level, criteria in self.thresholds.items():
            if (percentage_drop >= criteria['percentage_drop'] or 
                absolute_drop >= criteria['absolute_drop']):
                severity = criteria['severity']
                trigger_type = f'hrv_drop_{level}'
                recommendation = self._get_recommendation(level, percentage_drop)
                break
        
        if severity is None:
            return None
        
        # Additional context from recent window
        window = self.user_windows[user_id]
        recent_values = [e.value for e in window if e.timestamp > datetime.utcnow() - timedelta(hours=1)]
        
        context = {
            'window_size': len(window),
            'recent_avg': statistics.mean(recent_values) if recent_values else current_value,
            'recent_min': min(recent_values) if recent_values else current_value,
            'recent_max': max(recent_values) if recent_values else current_value,
            'quality_score': current_event.quality_score,
            'device_source': current_event.device_source,
            'baseline_sample_count': baseline_data.get('sample_count', 0)
        }
        
        # Check for sustained drop pattern
        if len(recent_values) >= 3:
            # If the last 3 readings are all below baseline - stddev, increase severity
            if all(v < baseline_value - stddev for v in recent_values[-3:]):
                severity = min(1.0, severity * 1.2)
                context['sustained_drop'] = True
        
        # Create trigger
        trigger = HRVTrigger(
            user_id=user_id,
            trigger_type=trigger_type,
            severity=severity,
            current_value=current_value,
            baseline_value=baseline_value,
            percentage_drop=percentage_drop,
            timestamp=current_event.timestamp,
            recommendation=recommendation,
            context=context
        )
        
        logger.info(f"HRV trigger detected for {user_id}: {percentage_drop:.1f}% drop, severity {severity}")
        
        return trigger
    
    def _get_recommendation(self, severity_level: str, percentage_drop: float) -> str:
        """
        Get initial recommendation based on severity level
        
        These are preliminary recommendations that will be refined
        by the Neuroscientist agent.
        """
        recommendations = {
            'critical': f"Significant HRV drop ({percentage_drop:.0f}%) detected. Immediate recovery focus recommended. Consider rest day and consult AUREN's Neuroscientist for personalized guidance.",
            'moderate': f"Moderate HRV drop ({percentage_drop:.0f}%) detected. Reduce training intensity and prioritize recovery. AUREN's Neuroscientist can provide specific recommendations.",
            'mild': f"Mild HRV drop ({percentage_drop:.0f}%) detected. Monitor closely and consider lighter training. Check in with AUREN for optimization tips."
        }
        
        return recommendations.get(severity_level, "HRV anomaly detected. Please consult AUREN for guidance.")


class HRVMonitoringService:
    """
    Service that continuously monitors biometric events and triggers interventions
    
    This service consumes from the Kafka biometric events topic and publishes
    triggers to the intervention topic when anomalies are detected.
    """
    
    def __init__(self):
        self.rule_engine = HRVRuleEngine()
        self.event_consumer = EventConsumer(['health.biometrics'])
        self.trigger_producer = EventProducer()
        self.running = False
    
    @otel_trace(operation_name="cep.monitoring_service")
    async def start(self):
        """
        Start the monitoring service
        
        This method runs continuously, processing events and generating
        triggers as needed.
        """
        self.running = True
        logger.info("Starting HRV monitoring service")
        
        try:
            async for event_data in self.event_consumer.consume_async():
                if not self.running:
                    break
                
                try:
                    # Parse biometric event
                    event = self._parse_biometric_event(event_data)
                    if event:
                        # Process through rule engine
                        trigger = await self.rule_engine.process_event(event)
                        
                        if trigger:
                            # Publish trigger event
                            await self._publish_trigger(trigger)
                            
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Critical error in monitoring service: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the monitoring service gracefully"""
        self.running = False
        await self.event_consumer.close()
        logger.info("HRV monitoring service stopped")
    
    def _parse_biometric_event(self, event_data: Dict[str, Any]) -> Optional[BiometricEvent]:
        """
        Parse raw event data into BiometricEvent object
        
        Handles various event formats and validates data integrity.
        """
        try:
            # Extract required fields
            user_id = event_data.get('user_id')
            metric_type = event_data.get('metric_type')
            value = event_data.get('value')
            timestamp_str = event_data.get('timestamp')
            
            if not all([user_id, metric_type, value, timestamp_str]):
                return None
            
            # Parse timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Create event object
            return BiometricEvent(
                user_id=user_id,
                metric_type=metric_type,
                value=float(value),
                timestamp=timestamp,
                device_source=event_data.get('device_source', 'unknown'),
                quality_score=float(event_data.get('quality_score', 1.0)),
                metadata=event_data.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"Error parsing biometric event: {e}")
            return None
    
    async def _publish_trigger(self, trigger: HRVTrigger):
        """
        Publish trigger event to Kafka for downstream processing
        
        The trigger will be consumed by the orchestrator to initiate
        a Neuroscientist consultation.
        """
        trigger_event = {
            'event_type': 'hrv_anomaly_detected',
            'user_id': trigger.user_id,
            'trigger_type': trigger.trigger_type,
            'severity': trigger.severity,
            'timestamp': trigger.timestamp.isoformat(),
            'data': {
                'current_value': trigger.current_value,
                'baseline_value': trigger.baseline_value,
                'percentage_drop': trigger.percentage_drop,
                'recommendation': trigger.recommendation,
                'context': trigger.context
            }
        }
        
        await self.trigger_producer.send(
            topic='triggers.detected',
            value=trigger_event,
            key=trigger.user_id
        )
        
        logger.info(f"Published HRV trigger for user {trigger.user_id}")


# Convenience function to run the monitoring service
def run_hrv_monitoring():
    """
    Run the HRV monitoring service
    
    This is the main entry point for the CEP monitoring system.
    """
    async def _run():
        service = HRVMonitoringService()
        
        # Handle graceful shutdown
        import signal
        
        def signal_handler(sig, frame):
            logger.info("Received shutdown signal")
            asyncio.create_task(service.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start monitoring
        await service.start()
    
    # Run the async service
    asyncio.run(_run())


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the monitoring service
    run_hrv_monitoring()
