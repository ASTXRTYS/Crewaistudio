"""
Event Store for AUREN Intelligence System
Provides event sourcing capabilities for audit trails and temporal analysis
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from data_layer.connection import DatabaseConnection, get_database_connection

logger = logging.getLogger(__name__)


class EventStreamType(Enum):
    """Types of event streams"""
    KNOWLEDGE = "knowledge"
    HYPOTHESIS = "hypothesis"
    VALIDATION = "validation"
    COLLABORATION = "collaboration"
    EMERGENCY = "emergency"
    SYSTEM = "system"


class EventStore:
    """
    Event store for AUREN intelligence system
    
    Features:
    - Event sourcing for audit trails
    - Temporal analysis capabilities
    - Real-time event streaming
    - Cross-agent event correlation
    - Performance analytics
    """
    
    def __init__(self, database_connection: Optional[DatabaseConnection] = None):
        """
        Initialize event store
        
        Args:
            database_connection: Database connection instance
        """
        self.db = database_connection or get_database_connection()
    
    async def initialize(self) -> bool:
        """
        Initialize the event store
        
        Returns:
            True if initialization successful
        """
        try:
            if not self.db.is_initialized:
                await self.db.initialize()
            
            # Initialize schema
            await self._initialize_schema()
            
            logger.info("✅ Event store initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize event store: {e}")
            return False
    
    async def _initialize_schema(self):
        """Initialize database schema"""
        
        schema_queries = [
            """
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                stream_id VARCHAR(255) NOT NULL,
                stream_type VARCHAR(100) NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                event_data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                INDEX idx_events_stream (stream_id),
                INDEX idx_events_type (stream_type),
                INDEX idx_events_event_type (event_type),
                INDEX idx_events_created (created_at DESC),
                INDEX idx_events_gin (event_data) USING GIN
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS event_streams (
                id SERIAL PRIMARY KEY,
                stream_id VARCHAR(255) UNIQUE NOT NULL,
                stream_type VARCHAR(100) NOT NULL,
                current_version INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                INDEX idx_streams_id (stream_id),
                INDEX idx_streams_type (stream_type),
                INDEX idx_streams_updated (updated_at DESC)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS event_subscriptions (
                id SERIAL PRIMARY KEY,
                subscription_id VARCHAR(255) UNIQUE NOT NULL,
                stream_type VARCHAR(100) NOT NULL,
                event_types JSONB DEFAULT '[]',
                callback_url VARCHAR(500),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                INDEX idx_subscriptions_type (stream_type),
                INDEX idx_subscriptions_active (is_active),
                INDEX idx_subscriptions_updated (updated_at DESC)
            )
            """
        ]
        
        for query in schema_queries:
            await self.db.execute(query)
    
    async def append_event(self,
                          stream_id: str,
                          stream_type: EventStreamType,
                          event_type: str,
                          event_data: Dict[str, Any],
                          metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Append event to stream
        
        Args:
            stream_id: Stream identifier
            stream_type: Type of stream
            event_type: Type of event
            event_data: Event data
            metadata: Optional metadata
            
        Returns:
            Event ID
        """
        query = """
            INSERT INTO events (stream_id, stream_type, event_type, event_data)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """
        
        # Add metadata to event data
        full_event_data = {
            **event_data,
            'metadata': metadata or {}
        }
        
        event_id = await self.db.fetchval(
            query,
            stream_id,
            stream_type.value,
            event_type,
            json.dumps(full_event_data)
        )
        
        # Update stream version
        await self._update_stream_version(stream_id, stream_type.value)
        
        return event_id
    
    async def get_events(self,
                        stream_id: str,
                        stream_type: Optional[EventStreamType] = None,
                        event_type: Optional[str] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get events from stream
        
        Args:
            stream_id: Stream identifier
            stream_type: Optional stream type filter
            event_type: Optional event type filter
            limit: Maximum events
            offset: Pagination offset
            
        Returns:
            List of events
        """
        query = """
            SELECT id, stream_id, stream_type, event_type, event_data, created_at
            FROM events
            WHERE stream_id = $1
              AND ($2::VARCHAR IS NULL OR stream_type = $2)
              AND ($3::VARCHAR IS NULL OR event_type = $3)
            ORDER BY created_at DESC, id DESC
            LIMIT $4 OFFSET $5
        """
        
        rows = await self.db.fetch(
            query, stream_id,
            stream_type.value if stream_type else None,
            event_type, limit, offset
        )
        
        return [dict(row) for row in rows]
    
    async def get_events_by_type(self,
                               stream_type: EventStreamType,
                               event_type: Optional[str] = None,
                               limit: int = 100,
                               offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get events by type
        
        Args:
            stream_type: Stream type
            event_type: Optional event type filter
            limit: Maximum events
            offset: Pagination offset
            
        Returns:
            List of events
        """
        query = """
            SELECT id, stream_id, stream_type, event_type, event_data, created_at
            FROM events
            WHERE stream_type = $1
              AND ($2::VARCHAR IS NULL OR event_type = $2)
            ORDER BY created_at DESC, id DESC
            LIMIT $3 OFFSET $4
        """
        
        rows = await self.db.fetch(
            query, stream_type.value, event_type, limit, offset
        )
        
        return [dict(row) for row in rows]
    
    async def get_events_by_user(self,
                              user_id: str,
                              stream_type: Optional[EventStreamType] = None,
                              event_type: Optional[str] = None,
                              limit: int = 100,
                              offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get events for user
        
        Args:
            user_id: User ID
            stream_type: Optional stream type filter
            event_type: Optional event type filter
            limit: Maximum events
            offset: Pagination offset
            
        Returns:
            List of events
        """
        # User events are typically in streams with user_id as stream_id
        return await self.get_events(
            stream_id=user_id,
            stream_type=stream_type,
            event_type=event_type,
            limit=limit,
            offset=offset
        )
    
    async def get_recent_events(self,
                             stream_type: Optional[EventStreamType] = None,
                             event_type: Optional[str] = None,
                             hours: int = 24,
                             limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent events
        
        Args:
            stream_type: Optional stream type filter
            event_type: Optional event type filter
            hours: Hours back
            limit: Maximum events
            
        Returns:
            List of recent events
        """
        query = """
            SELECT id, stream_id, stream_type, event_type, event_data, created_at
            FROM events
            WHERE created_at >= NOW() - INTERVAL '%s hours'
              AND ($1::VARCHAR IS NULL OR stream_type = $1)
              AND ($2::VARCHAR IS NULL OR event_type = $2)
            ORDER BY created_at DESC, id DESC
            LIMIT $3
        """ % hours
        
        rows = await self.db.fetch(
            query,
            stream_type.value if stream_type else None,
            event_type, limit
        )
        
        return [dict(row) for row in rows]
    
    async def get_event_count(self,
                           stream_id: str,
                           stream_type: Optional[EventStreamType] = None,
                           event_type: Optional[str] = None) -> int:
        """
        Get event count
        
        Args:
            stream_id: Stream identifier
            stream_type: Optional stream type filter
            event_type: Optional event type filter
            
        Returns:
            Event count
        """
        query = """
            SELECT COUNT(*) as count
            FROM events
            WHERE stream_id = $1
              AND ($2::VARCHAR IS NULL OR stream_type = $2)
              AND ($3::VARCHAR IS NULL OR event_type = $3)
        """
        
        result = await self.db.fetchval(
            query, stream_id,
            stream_type.value if stream_type else None,
            event_type
        )
        
        return result or 0
    
    async def get_event_statistics(self,
                                 stream_type: Optional[EventStreamType] = None,
                                 hours: int = 24) -> Dict[str, Any]:
        """
        Get event statistics
        
        Args:
            stream_type: Optional stream type filter
            hours: Hours back
            
        Returns:
            Event statistics
        """
        query = """
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT stream_id) as unique_streams,
                COUNT(DISTINCT event_type) as unique_event_types,
                MIN(created_at) as earliest_event,
                MAX(created_at) as latest_event
            FROM events
            WHERE created_at >= NOW() - INTERVAL '%s hours'
              AND ($1::VARCHAR IS NULL OR stream_type = $1)
        """ % hours
        
        result = await self.db.fetchrow(
            query, stream_type.value if stream_type else None
        )
        
        return dict(result) if result else {}
    
    async def search_events(self,
                        query: str,
                        stream_type: Optional[EventStreamType] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search events using full-text search
        
        Args:
            query: Search query
            stream_type: Optional stream type filter
            limit: Maximum results
            
        Returns:
            List of matching events
        """
        search_query = """
            SELECT id, stream_id, stream_type, event_type, event_data, created_at
            FROM events
            WHERE ($1::VARCHAR IS NULL OR stream_type = $1)
              AND (
                to_tsvector('english', event_data::text) @@ plainto_tsquery('english', $2)
                OR event_type ILIKE '%' || $2 || '%'
              )
            ORDER BY created_at DESC, id DESC
            LIMIT $3
        """
        
        rows = await self.db.fetch(
            search_query,
            stream_type.value if stream_type else None,
            query, limit
        )
        
        return [dict(row) for row in rows]
    
    async def get_event_stream(self,
                            stream_id: str,
                            from_event_id: Optional[int] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get event stream for replay
        
        Args:
            stream_id: Stream identifier
            from_event_id: Optional starting event ID
            limit: Maximum events
            
        Returns:
            List of events in chronological order
        """
        query = """
            SELECT id, stream_id, stream_type, event_type, event_data, created_at
            FROM events
            WHERE stream_id = $1
              AND ($2::INTEGER IS NULL OR id > $2)
            ORDER BY created_at ASC, id ASC
            LIMIT $3
        """
        
        rows = await self.db.fetch(query, stream_id, from_event_id, limit)
        return [dict(row) for row in rows]
    
    async def create_event_stream(self,
                               stream_id: str,
                               stream_type: EventStreamType) -> bool:
        """
        Create new event stream
        
        Args:
            stream_id: Stream identifier
            stream_type: Type of stream
            
        Returns:
            True if creation successful
        """
        query = """
            INSERT INTO event_streams (stream_id, stream_type)
            VALUES ($1, $2)
            ON CONFLICT (stream_id) DO NOTHING
        """
        
        result = await self.db.execute(query, stream_id, stream_type.value)
        return result == "INSERT 1"
    
    async def get_stream_version(self, stream_id: str) -> int:
        """
        Get current stream version
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            Current version number
        """
        query = """
            SELECT current_version
            FROM event_streams
            WHERE stream_id = $1
        """
        
        result = await self.db.fetchval(query, stream_id)
        return result or 0
    
    async def _update_stream_version(self, stream_id: str, stream_type: str):
        """Update stream version"""
        query = """
            INSERT INTO event_streams (stream_id, stream_type, current_version)
            VALUES ($1, $2, 1)
            ON CONFLICT (stream_id) DO UPDATE
            SET current_version = event_streams.current_version + 1,
                updated_at = NOW()
        """
        
        await self.db.execute(query, stream_id, stream_type)
    
    async def create_subscription(self,
                                subscription_id: str,
                                stream_type: EventStreamType,
                                event_types: List[str],
                                callback_url: Optional[str] = None) -> bool:
        """
        Create event subscription
        
        Args:
            subscription_id: Subscription identifier
            stream_type: Stream type
            event_types: List of event types to subscribe to
            callback_url: Optional callback URL
            
        Returns:
            True if creation successful
        """
        query = """
            INSERT INTO event_subscriptions (subscription_id, stream_type, event_types, callback_url)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (subscription_id) DO NOTHING
        """
        
        result = await self.db.execute(
            query,
            subscription_id,
            stream_type.value,
            json.dumps(event_types),
            callback_url
        )
        
        return result == "INSERT 1"
    
    async def get_subscriptions(self,
                           stream_type: EventStreamType,
                           event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get active subscriptions
        
        Args:
            stream_type: Stream type
            event_type: Optional event type filter
            
        Returns:
            List of active subscriptions
        """
        query = """
            SELECT subscription_id, stream_type, event_types, callback_url, created_at
            FROM event_subscriptions
            WHERE stream_type = $1
              AND is_active = TRUE
              AND ($2::VARCHAR IS NULL OR $2 = ANY(event_types))
            ORDER BY created_at DESC
        """
        
        rows = await self.db.fetch(query, stream_type.value, event_type)
        return [dict(row) for row in rows]
    
    async def cleanup(self):
        """Clean up resources"""
        await self.db.cleanup()


# Utility functions
async def create_event_store() -> EventStore:
    """
    Create and initialize event store
    
    Returns:
        Initialized event store
    """
    store = EventStore()
    await store.initialize()
    return store


async def test_event_store():
    """
    Test the event store
    """
    store = await create_event_store()
    
    try:
        # Test event storage
        event_id = await store.append_event(
            stream_id="test_user",
            stream_type=EventStreamType.KNOWLEDGE,
            event_type="knowledge_created",
            event_data={"knowledge_id": "test_001", "title": "Test Knowledge"}
        )
        print(f"Stored event: {event_id}")
        
        # Test event retrieval
        events = await store.get_events(
            stream_id="test_user",
            stream_type=EventStreamType.KNOWLEDGE,
            limit=10
        )
        print(f"Retrieved {len(events)} events")
        
        # Test recent events
        recent = await store.get_recent_events(
            stream_type=EventStreamType.KNOWLEDGE,
            hours=1,
            limit=10
        )
        print(f"Recent events: {len(recent)}")
        
        # Test statistics
        stats = await store.get_event_statistics(
            stream_type=EventStreamType.KNOWLEDGE,
            hours=1
        )
        print(f"Event stats: {stats}")
        
    finally:
        await store.cleanup()


if __name__ == "__main__":
    asyncio.run(test_event_store())
