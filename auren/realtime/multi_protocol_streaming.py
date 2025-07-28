"""
Flexible event streaming supporting both Redis Streams and Kafka
Provides multiple streaming options for different deployment scenarios
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime, timezone
import redis.asyncio as redis
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import socket

from auren.realtime.langgraph_instrumentation import AURENStreamEvent, AURENPerformanceMetrics
from dataclasses import asdict

logger = logging.getLogger(__name__)

class EventStreamer(ABC):
    """Abstract base class for event streaming implementations"""
    
    @abstractmethod
    async def stream_event(self, event: AURENStreamEvent) -> bool:
        """Stream an event to the messaging system"""
        pass
    
    @abstractmethod
    async def subscribe_to_events(self, consumer_id: str, event_types: List[str] = None) -> AsyncIterator:
        """Subscribe to event stream"""
        pass
    
    @abstractmethod
    async def get_recent_events(self, limit: int = 100, event_types: List[str] = None) -> List[Dict]:
        """Get recent events for replay"""
        pass

class RedisStreamEventStreamer(EventStreamer):
    """Redis Streams implementation for high-performance, low-latency streaming"""
    
    def __init__(self, redis_url: str, stream_name: str = "auren:events"):
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.redis_client = None
        self.events_sent = 0
        
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(self.redis_url)
        await self.redis_client.ping()
        logger.info(f"Redis event streamer initialized on {self.redis_url}")
    
    async def stream_event(self, event: AURENStreamEvent) -> bool:
        """Stream event to Redis Stream"""
        try:
            event_data = {
                "event_id": event.event_id,
                "trace_id": event.trace_id or "",
                "session_id": event.session_id or "",
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "source_agent": json.dumps(event.source_agent or {}),
                "target_agent": json.dumps(event.target_agent or {}),
                "payload": json.dumps(event.payload),
                "metadata": json.dumps(event.metadata),
                "user_id": event.user_id or ""
            }
            
            # Add performance metrics if available
            if event.performance_metrics:
                event_data["performance_metrics"] = json.dumps(asdict(event.performance_metrics))
            
            # Add to Redis Stream
            await self.redis_client.xadd(
                self.stream_name,
                event_data,
                maxlen=50000  # Keep last 50k events
            )
            
            # Also add to time-series for analytics
            await self.redis_client.zadd(
                f"events:by_type:{event.event_type.value}",
                {event.event_id: event.timestamp.timestamp()},
                nx=True
            )
            
            self.events_sent += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to stream event to Redis: {e}")
            return False
    
    async def subscribe_to_events(self, consumer_id: str, event_types: List[str] = None):
        """Subscribe to Redis Stream"""
        try:
            consumer_group = f"dashboard_consumers"
            
            # Create consumer group if it doesn't exist
            try:
                await self.redis_client.xgroup_create(
                    self.stream_name, consumer_group, id="0", mkstream=True
                )
            except redis.RedisError:
                pass  # Group already exists
            
            while True:
                try:
                    # Read from stream
                    messages = await self.redis_client.xreadgroup(
                        consumer_group,
                        consumer_id,
                        {self.stream_name: ">"},
                        count=10,
                        block=1000
                    )
                    
                    for stream, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            try:
                                # Parse event
                                event_data = self._parse_redis_event(fields)
                                
                                # Filter by event types if specified
                                if event_types and event_data.get("event_type") not in event_types:
                                    continue
                                
                                yield event_data
                                
                                # Acknowledge message
                                await self.redis_client.xack(self.stream_name, consumer_group, message_id)
                                
                            except Exception as e:
                                logger.error(f"Error processing Redis message: {e}")
                                
                except redis.RedisError as e:
                    logger.error(f"Redis stream read error: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Redis subscription error: {e}")
    
    async def get_recent_events(self, limit: int = 100, event_types: List[str] = None) -> List[Dict]:
        """Get recent events from Redis Stream"""
        try:
            # Read recent events from stream
            messages = await self.redis_client.xrevrange(
                self.stream_name,
                count=limit
            )
            
            events = []
            for message_id, fields in messages:
                try:
                    event_data = self._parse_redis_event(fields)
                    
                    # Filter by event types if specified
                    if event_types and event_data.get("event_type") not in event_types:
                        continue
                    
                    events.append(event_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing Redis event: {e}")
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting recent events from Redis: {e}")
            return []
    
    def _parse_redis_event(self, fields: Dict) -> Dict:
        """Parse Redis event fields into event dictionary"""
        try:
            return {
                "event_id": fields.get(b"event_id", b"").decode(),
                "trace_id": fields.get(b"trace_id", b"").decode() or None,
                "session_id": fields.get(b"session_id", b"").decode() or None,
                "timestamp": fields.get(b"timestamp", b"").decode(),
                "event_type": fields.get(b"event_type", b"").decode(),
                "source_agent": json.loads(fields.get(b"source_agent", b"{}").decode()),
                "target_agent": json.loads(fields.get(b"target_agent", b"{}").decode()),
                "payload": json.loads(fields.get(b"payload", b"{}").decode()),
                "metadata": json.loads(fields.get(b"metadata", b"{}").decode()),
                "performance_metrics": json.loads(fields.get(b"performance_metrics", b"{}").decode()) if b"performance_metrics" in fields else None,
                "user_id": fields.get(b"user_id", b"").decode() or None
            }
        except Exception as e:
            logger.error(f"Error parsing Redis event fields: {e}")
            return {}

class KafkaEventStreamer(EventStreamer):
    """Kafka implementation for distributed, high-throughput streaming"""
    
    def __init__(self, bootstrap_servers: str, topic: str = "auren-events"):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = None
        self.events_sent = 0
        
    async def initialize(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=socket.gethostname(),
                acks='all',  # Ensure message durability
                retries=3,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            logger.info(f"Kafka event streamer initialized on {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    async def stream_event(self, event: AURENStreamEvent) -> bool:
        """Stream event to Kafka topic"""
        try:
            event_data = {
                "event_id": event.event_id,
                "trace_id": event.trace_id,
                "session_id": event.session_id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "source_agent": event.source_agent,
                "target_agent": event.target_agent,
                "payload": event.payload,
                "metadata": event.metadata,
                "user_id": event.user_id
            }
            
            # Add performance metrics if available
            if event.performance_metrics:
                event_data["performance_metrics"] = asdict(event.performance_metrics)
            
            # Send to Kafka
            future = self.producer.send(
                self.topic,
                key=event.trace_id,  # Partition by trace_id
                value=event_data
            )
            
            # Wait for send to complete (with timeout)
            record_metadata = future.get(timeout=10)
            
            self.events_sent += 1
            logger.debug(f"Event sent to Kafka topic {record_metadata.topic} partition {record_metadata.partition}")
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka error streaming event: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to stream event to Kafka: {e}")
            return False
    
    async def subscribe_to_events(self, consumer_id: str, event_types: List[str] = None):
        """Subscribe to Kafka topic"""
        try:
            consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"dashboard_consumers",
                client_id=consumer_id,
                auto_offset_reset='latest',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=1000
            )
            
            for message in consumer:
                try:
                    event_data = message.value
                    
                    # Filter by event types if specified
                    if event_types and event_data.get("event_type") not in event_types:
                        continue
                    
                    yield event_data
                    
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}")
                    
        except Exception as e:
            logger.error(f"Kafka subscription error: {e}")
    
    async def get_recent_events(self, limit: int = 100, event_types: List[str] = None) -> List[Dict]:
        """Get recent events from Kafka (limited functionality)"""
        # Note: Kafka doesn't easily support recent event queries
        # This would typically be implemented with a separate event store
        logger.warning("Recent events query not fully supported with Kafka - use Redis Streams for this feature")
        return []

class HybridEventStreamer(EventStreamer):
    """Hybrid implementation supporting both Redis and Kafka"""
    
    def __init__(self, redis_url: str, kafka_servers: str):
        self.redis_streamer = RedisStreamEventStreamer(redis_url)
        self.kafka_streamer = KafkaEventStreamer(kafka_servers)
        
    async def initialize(self):
        """Initialize both streamers"""
        await self.redis_streamer.initialize()
        await self.kafka_streamer.initialize()
        logger.info("Hybrid event streamer initialized")
    
    async def stream_event(self, event: AURENStreamEvent) -> bool:
        """Stream to both Redis and Kafka"""
        redis_success = await self.redis_streamer.stream_event(event)
        kafka_success = await self.kafka_streamer.stream_event(event)
        
        # Consider success if at least one succeeds
        return redis_success or kafka_success
    
    async def subscribe_to_events(self, consumer_id: str, event_types: List[str] = None):
        """Subscribe to Redis (prefer Redis for real-time)"""
        async for event in self.redis_streamer.subscribe_to_events(consumer_id, event_types):
            yield event
    
    async def get_recent_events(self, limit: int = 100, event_types: List[str] = None) -> List[Dict]:
        """Get recent events from Redis"""
        return await self.redis_streamer.get_recent_events(limit, event_types) 