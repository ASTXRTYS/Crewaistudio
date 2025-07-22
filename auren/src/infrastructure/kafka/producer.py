"""
Kafka producer for AUREN's event pipeline.

Handles production of all event types with proper serialization,
error handling, and audit logging for HIPAA compliance.
"""

from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging
import json
from typing import Optional, Callable
from datetime import datetime

from src.config.settings import settings
from src.infrastructure.schemas.health_events import (
    HealthBiometricEvent,
    TriggerEvent,
    ConversationEvent,
    SystemEvent,
    EventEnvelope
)

logger = logging.getLogger(__name__)


class EventProducer:
    """Thread-safe Kafka producer for AUREN events"""
    
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=settings.kafka.bootstrap_servers,
            value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v,
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            compression_type=None,  # Changed from 'snappy' to avoid dependency issues
            retries=3,
            acks='all',  # Wait for all replicas
            max_in_flight_requests_per_connection=5,
            client_id='auren-event-producer',
            # Add timeout configurations
            request_timeout_ms=30000,      # 30 seconds
            api_version_auto_timeout_ms=10000,  # 10 seconds
            max_block_ms=60000,            # 60 seconds
            retry_backoff_ms=100
        )
        self._delivery_reports = []
    
    def send_biometric_event(
        self, 
        event: HealthBiometricEvent,
        callback: Optional[Callable] = None
    ) -> None:
        """Send a biometric event to Kafka"""
        try:
            future = self.producer.send(
                topic=settings.kafka.health_biometrics_topic,
                key=event.user_id,
                value=event.to_json(),
                timestamp_ms=int(event.timestamp.timestamp() * 1000)
            )
            
            if callback:
                future.add_callback(callback)
            
            # Log for audit trail (HIPAA requirement)
            logger.info(
                f"Sent biometric event: type={event.event_type.value}, "
                f"user={event.user_id[:8]}..., event_id={event.event_id}"
            )
            
        except KafkaError as e:
            logger.error(f"Failed to send biometric event: {e}")
            raise
    
    def send_trigger_event(
        self,
        event: TriggerEvent,
        callback: Optional[Callable] = None
    ) -> None:
        """Send a trigger event to Kafka"""
        try:
            future = self.producer.send(
                topic=settings.kafka.triggers_detected_topic,
                key=event.user_id,
                value=event.to_json(),
                timestamp_ms=int(event.timestamp.timestamp() * 1000)
            )
            
            if callback:
                future.add_callback(callback)
            
            logger.info(
                f"Sent trigger event: type={event.trigger_type.value}, "
                f"severity={event.severity}, user={event.user_id[:8]}..."
            )
            
        except KafkaError as e:
            logger.error(f"Failed to send trigger event: {e}")
            raise
    
    def send_conversation_event(
        self,
        event: ConversationEvent,
        callback: Optional[Callable] = None
    ) -> None:
        """Send a conversation event to Kafka"""
        try:
            future = self.producer.send(
                topic=settings.kafka.conversations_events_topic,
                key=event.user_id,
                value=event.to_json(),
                timestamp_ms=int(event.timestamp.timestamp() * 1000)
            )
            
            if callback:
                future.add_callback(callback)
            
            logger.info(
                f"Sent conversation event: type={event.message_type}, "
                f"specialist={event.specialist_id}, user={event.user_id[:8]}..."
            )
            
        except KafkaError as e:
            logger.error(f"Failed to send conversation event: {e}")
            raise
    
    def send_system_event(
        self,
        event: SystemEvent,
        callback: Optional[Callable] = None
    ) -> None:
        """Send a system event to Kafka"""
        try:
            future = self.producer.send(
                topic="system.events",
                key=event.component,
                value=event.to_json(),
                timestamp_ms=int(event.timestamp.timestamp() * 1000)
            )
            
            if callback:
                future.add_callback(callback)
            
            logger.info(
                f"Sent system event: type={event.event_type}, "
                f"component={event.component}, severity={event.severity}"
            )
            
        except KafkaError as e:
            logger.error(f"Failed to send system event: {e}")
            raise
    
    def send_envelope(
        self,
        envelope: EventEnvelope,
        topic: str,
        callback: Optional[Callable] = None
    ) -> None:
        """Send a generic event envelope to any topic"""
        try:
            future = self.producer.send(
                topic=topic,
                key=envelope.source,
                value=envelope.to_json(),
                timestamp_ms=int(envelope.timestamp.timestamp() * 1000)
            )
            
            if callback:
                future.add_callback(callback)
            
            logger.info(
                f"Sent envelope: type={envelope.event_type}, "
                f"source={envelope.source}, topic={topic}"
            )
            
        except KafkaError as e:
            logger.error(f"Failed to send envelope: {e}")
            raise
    
    def flush(self, timeout: Optional[float] = None) -> None:
        """Flush all pending messages"""
        self.producer.flush(timeout=timeout)
    
    def close(self) -> None:
        """Close the producer connection"""
        self.flush()
        self.producer.close()
    
    def get_delivery_reports(self) -> list:
        """Get delivery reports for monitoring"""
        return self._delivery_reports.copy()
