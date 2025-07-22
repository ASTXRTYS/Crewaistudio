"""
Kafka consumer for AUREN's event pipeline.

Handles consumption of all event types with proper deserialization,
error handling, and processing for HIPAA compliance.
"""

from kafka import KafkaConsumer
from kafka.errors import KafkaError
import logging
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

from src.config.settings import settings
from src.infrastructure.schemas.health_events import (
    HealthBiometricEvent,
    TriggerEvent,
    ConversationEvent,
    SystemEvent,
    EventEnvelope
)

logger = logging.getLogger(__name__)


class EventConsumer:
    """Thread-safe Kafka consumer for AUREN events"""
    
    def __init__(self, group_id: str = "auren-event-processor"):
        self.group_id = group_id
        self.consumer = KafkaConsumer(
            bootstrap_servers=settings.kafka.bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda v: v.decode('utf-8') if isinstance(v, bytes) else v,
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            enable_auto_commit=False,
            auto_offset_reset='earliest',
            client_id=f'auren-event-consumer-{group_id}',
            max_poll_records=100,
            session_timeout_ms=30000,      # Already set
            heartbeat_interval_ms=3000,    # Already set
            # Add additional timeout configurations
            request_timeout_ms=30000,      # 30 seconds
            api_version_auto_timeout_ms=10000  # 10 seconds
        )
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.handlers = {
            'health.biometrics': self._handle_biometric_event,
            'triggers.detected': self._handle_trigger_event,
            'conversations.events': self._handle_conversation_event,
            'system.events': self._handle_system_event
        }
    
    def subscribe(self, topics: List[str]) -> None:
        """Subscribe to topics"""
        self.consumer.subscribe(topics)
        logger.info(f"Subscribed to topics: {topics}")
    
    def start_processing(
        self,
        handlers: Optional[Dict[str, Callable]] = None,
        auto_commit: bool = True
    ) -> None:
        """Start processing events"""
        if handlers:
            self.handlers.update(handlers)
        
        self.running = True
        logger.info(f"Starting event processing for group: {self.group_id}")
        
        try:
            while self.running:
                # Poll for messages
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        self._process_message(message, auto_commit)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
            raise
        finally:
            self.stop_processing()
    
    def _process_message(self, message, auto_commit: bool):
        """Process a single message"""
        try:
            topic = message.topic
            key = message.key
            value = message.value
            
            logger.debug(
                f"Processing message: topic={topic}, "
                f"partition={message.partition}, offset={message.offset}"
            )
            
            # Route to appropriate handler
            if topic in self.handlers:
                self.handlers[topic](value, key, message)
            else:
                logger.warning(f"No handler for topic: {topic}")
            
            # Commit offset if auto-commit is disabled
            if not auto_commit:
                self.consumer.commit()
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Could implement retry logic here
    
    def _handle_biometric_event(self, value: str, key: str, message):
        """Handle biometric events"""
        try:
            event = HealthBiometricEvent.from_json(value)
            logger.info(
                f"Processed biometric event: type={event.event_type.value}, "
                f"user={event.user_id[:8]}..., event_id={event.event_id}"
            )
            
            # Here you would add business logic for processing biometric events
            # For example: trigger analysis, update user profile, etc.
            
        except Exception as e:
            logger.error(f"Error processing biometric event: {e}")
    
    def _handle_trigger_event(self, value: str, key: str, message):
        """Handle trigger events"""
        try:
            event = TriggerEvent.from_json(value)
            logger.info(
                f"Processed trigger event: type={event.trigger_type.value}, "
                f"severity={event.severity}, user={event.user_id[:8]}..."
            )
            
            # Here you would add business logic for processing triggers
            # For example: notify specialists, update risk scores, etc.
            
        except Exception as e:
            logger.error(f"Error processing trigger event: {e}")
    
    def _handle_conversation_event(self, value: str, key: str, message):
        """Handle conversation events"""
        try:
            event = ConversationEvent.from_json(value)
            logger.info(
                f"Processed conversation event: type={event.message_type}, "
                f"specialist={event.specialist_id}, user={event.user_id[:8]}..."
            )
            
            # Here you would add business logic for processing conversations
            # For example: update conversation state, trigger responses, etc.
            
        except Exception as e:
            logger.error(f"Error processing conversation event: {e}")
    
    def _handle_system_event(self, value: str, key: str, message):
        """Handle system events"""
        try:
            event = SystemEvent.from_json(value)
            logger.info(
                f"Processed system event: type={event.event_type}, "
                f"component={event.component}, severity={event.severity}"
            )
            
            # Here you would add business logic for processing system events
            # For example: health checks, alerts, etc.
            
        except Exception as e:
            logger.error(f"Error processing system event: {e}")
    
    def start_async_processing(
        self,
        handlers: Optional[Dict[str, Callable]] = None
    ) -> threading.Thread:
        """Start processing in a separate thread"""
        thread = threading.Thread(
            target=self.start_processing,
            kwargs={'handlers': handlers, 'auto_commit': True}
        )
        thread.daemon = True
        thread.start()
        return thread
    
    def stop_processing(self) -> None:
        """Stop processing events"""
        self.running = False
        self.consumer.close()
        self.executor.shutdown(wait=True)
        logger.info("Consumer stopped")
    
    def get_lag(self) -> Dict[str, int]:
        """Get consumer lag for monitoring"""
        try:
            partitions = self.consumer.assignment()
            lag = {}
            for partition in partitions:
                position = self.consumer.position(partition)
                end_offset = self.consumer.end_offsets([partition])[partition]
                lag[partition.topic] = end_offset - position
            return lag
        except Exception as e:
            logger.error(f"Error getting lag: {e}")
            return {}
    
    def pause(self, partitions: List[Any]) -> None:
        """Pause consumption for specified partitions"""
        self.consumer.pause(*partitions)
        logger.info(f"Paused partitions: {partitions}")
    
    def resume(self, partitions: List[Any]) -> None:
        """Resume consumption for specified partitions"""
        self.consumer.resume(*partitions)
        logger.info(f"Resumed partitions: {partitions}")
    
    def close(self) -> None:
        """Close the consumer"""
        self.stop_processing()


class HealthEventConsumer(EventConsumer):
    """Specialized consumer for health events"""
    
    def __init__(self):
        super().__init__(group_id="auren-health-processor")
        self.subscribe([
            settings.kafka.health_biometrics_topic,
            settings.kafka.triggers_detected_topic
        ])


class ConversationConsumer(EventConsumer):
    """Specialized consumer for conversation events"""
    
    def __init__(self):
        super().__init__(group_id="auren-conversation-processor")
        self.subscribe([settings.kafka.conversations_events_topic])


class SystemConsumer(EventConsumer):
    """Specialized consumer for system events"""
    
    def __init__(self):
        super().__init__(group_id="auren-system-processor")
        self.subscribe(["system.events"])


class MultiTopicConsumer(EventConsumer):
    """Consumer that can handle multiple topics"""
    
    def __init__(self, topics: List[str], group_id: str):
        super().__init__(group_id=group_id)
        self.subscribe(topics)
