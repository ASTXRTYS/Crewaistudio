"""
Event Store Implementation
Provides immutable audit trails and event sourcing capabilities
"""

import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
import asyncpg
import logging

logger = logging.getLogger(__name__)

class EventType(Enum):
    """All event types in the AUREN system"""
    MEMORY_CREATED = "memory_created"
    MEMORY_UPDATED = "memory_updated"
    MEMORY_DELETED = "memory_deleted"
    AGENT_DECISION = "agent_decision"
    USER_INTERACTION = "user_interaction"
    HYPOTHESIS_FORMED = "hypothesis_formed"
    HYPOTHESIS_VALIDATED = "hypothesis_validated"
    KNOWLEDGE_SHARED = "knowledge_shared"
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ENDED = "conversation_ended"
    BIOMETRIC_DATA_RECEIVED = "biometric_data_received"
    GOAL_UPDATED = "goal_updated"
    PREFERENCE_CHANGED = "preference_changed"

class Event:
    """Represents a single event in the event store"""
    
    def __init__(self, event_id: str, stream_id: str, event_type: EventType, 
                 version: int, payload: Dict[str, Any], 
                 metadata: Dict[str, Any] = None, created_at: datetime = None):
        self.event_id = event_id
        self.stream_id = stream_id
        self.event_type = event_type
        self.version = version
        self.payload = payload
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for storage"""
        return {
            'event_id': self.event_id,
            'stream_id': self.stream_id,
            'event_type': self.event_type.value,
            'version': self.version,
            'payload': self.payload,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }

class ConcurrencyError(Exception):
    """Raised when optimistic concurrency control detects a conflict"""
    pass

class EventStore:
    """
    Event store implementation using PostgreSQL
    Provides immutable audit trails and event sourcing capabilities
    """
    
    def __init__(self, connection_manager=None):
        self.connection_manager = connection_manager
        self._event_handlers: List[Callable] = []
    
    async def initialize(self) -> None:
        """Initialize the event store schema"""
        schema_sql = """
        -- Enable UUID extension
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Global sequence for event ordering
        CREATE SEQUENCE IF NOT EXISTS global_event_sequence;
        
        -- Core events table
        CREATE TABLE IF NOT EXISTS events (
            sequence_id BIGINT PRIMARY KEY DEFAULT nextval('global_event_sequence'),
            event_id UUID NOT NULL UNIQUE DEFAULT uuid_generate_v4(),
            stream_id UUID NOT NULL,
            event_type VARCHAR(255) NOT NULL,
            version INTEGER NOT NULL,
            payload JSONB NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT unique_stream_version UNIQUE (stream_id, version)
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_events_stream ON events(stream_id, version);
        CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
        CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_events_stream_type ON events(stream_id, event_type);
        
        -- Listen/NOTIFY for real-time updates
        CREATE OR REPLACE FUNCTION notify_event_insert() RETURNS TRIGGER AS $$
        BEGIN
            PERFORM pg_notify('events_channel', json_build_object(
                'event_id', NEW.event_id,
                'event_type', NEW.event_type,
                'stream_id', NEW.stream_id,
                'payload', NEW.payload
            )::text);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER IF NOT EXISTS events_notify_trigger
            AFTER INSERT ON events
            FOR EACH ROW
            EXECUTE FUNCTION notify_event_insert();
        """
        
        from .connection import AsyncPostgresManager
        
        async with AsyncPostgresManager.connection() as conn:
            await conn.execute(schema_sql)
            logger.info("Event store schema initialized")
    
    async def append_event(self, stream_id: str, event_type: EventType, 
                          payload: Dict[str, Any], expected_version: Optional[int] = None,
                          metadata: Dict[str, Any] = None) -> Event:
        """
        Append an event to the event store
        
        Args:
            stream_id: Unique identifier for the event stream
            event_type: Type of event being stored
            payload: Event data
            expected_version: Expected version for optimistic concurrency control
            metadata: Additional metadata about the event
            
        Returns:
            Event: The created event
            
        Raises:
            ConcurrencyError: If optimistic concurrency control detects a conflict
        """
        from .connection import AsyncPostgresManager
        
        metadata = metadata or {}
        
        async with AsyncPostgresManager.connection() as conn:
            # Get current version if not provided
            if expected_version is None:
                current_version = await conn.fetchval(
                    "SELECT COALESCE(MAX(version), 0) FROM events WHERE stream_id = $1",
                    stream_id
                )
                expected_version = current_version
            
            # Check for concurrency conflict
            if expected_version > 0:
                existing = await conn.fetchval(
                    "SELECT version FROM events WHERE stream_id = $1 AND version = $2",
                    stream_id, expected_version
                )
                if existing is None:
                    raise ConcurrencyError(
                        f"Expected version {expected_version} but stream {stream_id} "
                        f"has different version"
                    )
            
            # Calculate next version
            next_version = expected_version + 1
            
            # Insert the event
            event_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO events (event_id, stream_id, event_type, version, payload, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                event_id, stream_id, event_type.value, next_version, 
                json.dumps(payload), json.dumps(metadata)
            )
            
            event = Event(
                event_id=event_id,
                stream_id=stream_id,
                event_type=event_type,
                version=next_version,
                payload=payload,
                metadata=metadata
            )
            
            # Notify event handlers
            await self._notify_handlers(event)
            
            return event
    
    async def get_stream_events(self, stream_id: str, from_version: int = 0, 
                               to_version: Optional[int] = None) -> List[Event]:
        """Get all events for a specific stream"""
        from .connection import AsyncPostgresManager
        
        async with AsyncPostgresManager.connection() as conn:
            query = """
                SELECT event_id, stream_id, event_type, version, payload, metadata, created_at
                FROM events
                WHERE stream_id = $1 AND version > $2
            """
            params = [stream_id, from_version]
            
            if to_version:
                query += " AND version <= $3"
                params.append(to_version)
            
            query += " ORDER BY version ASC"
            
            rows = await conn.fetch(query, *params)
            
            events = []
            for row in rows:
                events.append(Event(
                    event_id=row['event_id'],
                    stream_id=row['stream_id'],
                    event_type=EventType(row['event_type']),
                    version=row['version'],
                    payload=row['payload'],
                    metadata=row['metadata'],
                    created_at=row['created_at']
                ))
            
            return events
    
    async def get_events_by_type(self, event_type: EventType, 
                               limit: int = 100) -> List[Event]:
        """Get events by type, ordered by creation time"""
        from .connection import AsyncPostgresManager
        
        async with AsyncPostgresManager.connection() as conn:
            rows = await conn.fetch(
                """
                SELECT event_id, stream_id, event_type, version, payload, metadata, created_at
                FROM events
                WHERE event_type = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                event_type.value, limit
            )
            
            events = []
            for row in rows:
                events.append(Event(
                    event_id=row['event_id'],
                    stream_id=row['stream_id'],
                    event_type=EventType(row['event_type']),
                    version=row['version'],
                    payload=row['payload'],
                    metadata=row['metadata'],
                    created_at=row['created_at']
                ))
            
            return events
    
    async def subscribe(self, handler: Callable[[Event], None]) -> None:
        """Subscribe to events for real-time processing"""
        self._event_handlers.append(handler)
    
    async def _notify_handlers(self, event: Event) -> None:
        """Notify all registered event handlers"""
        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    async def replay_events(self, stream_id: str, handler: Callable[[Event], None]) -> None:
        """Replay all events for a stream to rebuild state"""
        events = await self.get_stream_events(stream_id)
        for event in events:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error replaying event {event.event_id}: {e}")
    
    async def get_event_count(self, stream_id: Optional[str] = None) -> int:
        """Get total event count, optionally filtered by stream"""
        from .connection import AsyncPostgresManager
        
        async with AsyncPostgresManager.connection() as conn:
            if stream_id:
                return await conn.fetchval(
                    "SELECT COUNT(*) FROM events WHERE stream_id = $1",
                    stream_id
                )
            else:
                return await conn.fetchval("SELECT COUNT(*) FROM events")
