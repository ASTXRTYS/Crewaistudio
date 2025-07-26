"""
PostgreSQL Tier - Long-term Structured Memory with Event Emission
Implements Tier 2 of the three-tier memory system with WebSocket integration
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import asyncpg

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory stored in the system"""
    FACT = "fact"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    HYPOTHESIS = "hypothesis"
    INSIGHT = "insight"
    CONVERSATION = "conversation"
    DECISION = "decision"
    KNOWLEDGE = "knowledge"


@dataclass
class PostgresMemoryItem:
    """Memory item for PostgreSQL storage"""
    memory_id: str
    agent_id: str
    user_id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    confidence: float
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_event_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_deleted: bool = False
    embedding: Optional[List[float]] = None


class EventType(Enum):
    """Event types for audit trail"""
    MEMORY_CREATED = "memory_created"
    MEMORY_UPDATED = "memory_updated"
    MEMORY_DELETED = "memory_deleted"
    MEMORY_RETRIEVED = "memory_retrieved"
    MEMORY_PROMOTED = "memory_promoted"
    MEMORY_DEMOTED = "memory_demoted"


class PostgreSQLTier:
    """
    Tier 2: Structured Long-term Memory with Event Sourcing
    
    Features:
    - ACID compliant storage
    - Event sourcing for complete audit trail
    - WebSocket event emission for real-time updates
    - Automatic schema management
    - Query optimization with indexes
    """
    
    def __init__(self, 
                 pool: Optional[asyncpg.Pool] = None,
                 database_url: Optional[str] = None,
                 event_emitter=None):
        self.pool = pool
        self.database_url = database_url or "postgresql://localhost/auren"
        self.event_emitter = event_emitter
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection and schema"""
        if self._initialized:
            return
        
        try:
            # Create connection pool if not provided
            if not self.pool:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=10,
                    max_size=50,
                    command_timeout=30.0
                )
            
            # Create schema
            await self._create_schema()
            
            self._initialized = True
            logger.info("PostgreSQL tier initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL tier: {e}")
            raise
    
    async def _create_schema(self):
        """Create database schema if not exists"""
        schema_sql = """
        -- Enable UUID extension
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Global sequence for event ordering
        CREATE SEQUENCE IF NOT EXISTS global_event_sequence;
        
        -- Core events table (immutable audit trail)
        CREATE TABLE IF NOT EXISTS events (
            sequence_id BIGINT PRIMARY KEY DEFAULT nextval('global_event_sequence'),
            event_id UUID NOT NULL UNIQUE DEFAULT uuid_generate_v4(),
            stream_id UUID NOT NULL,
            event_type VARCHAR(255) NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            payload JSONB NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            
            -- Optimistic concurrency control
            CONSTRAINT unique_stream_version UNIQUE (stream_id, version)
        );
        
        -- Agent memories table (projection)
        CREATE TABLE IF NOT EXISTS agent_memories (
            memory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            agent_id VARCHAR(255) NOT NULL,
            user_id UUID,
            memory_type VARCHAR(100) NOT NULL,
            content JSONB NOT NULL,
            metadata JSONB DEFAULT '{}',
            confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            expires_at TIMESTAMPTZ,
            is_deleted BOOLEAN DEFAULT FALSE,
            source_event_id UUID REFERENCES events(event_id),
            embedding VECTOR(1536)  -- For future semantic search
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_events_stream_id ON events(stream_id);
        CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
        CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at DESC);
        
        CREATE INDEX IF NOT EXISTS idx_memories_agent_user 
            ON agent_memories(agent_id, user_id) WHERE NOT is_deleted;
        CREATE INDEX IF NOT EXISTS idx_memories_type 
            ON agent_memories(memory_type) WHERE NOT is_deleted;
        CREATE INDEX IF NOT EXISTS idx_memories_created 
            ON agent_memories(created_at DESC) WHERE NOT is_deleted;
        CREATE INDEX IF NOT EXISTS idx_memories_content_gin 
            ON agent_memories USING GIN(content);
        
        -- Trigger for updated_at
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_memories_updated_at 
            BEFORE UPDATE ON agent_memories
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
        -- Real-time notification function
        CREATE OR REPLACE FUNCTION notify_memory_event()
        RETURNS TRIGGER AS $$
        BEGIN
            PERFORM pg_notify('memory_events', 
                json_build_object(
                    'sequence_id', NEW.sequence_id,
                    'event_id', NEW.event_id,
                    'stream_id', NEW.stream_id,
                    'event_type', NEW.event_type,
                    'created_at', NEW.created_at
                )::text
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Trigger for real-time notifications
        CREATE TRIGGER trigger_memory_event_notification
            AFTER INSERT ON events
            FOR EACH ROW
            EXECUTE FUNCTION notify_memory_event();
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
    
    async def store_memory(self,
                          memory_id: Optional[str] = None,
                          agent_id: str = None,
                          user_id: str = None,
                          memory_type: Union[str, MemoryType] = None,
                          content: Dict[str, Any] = None,
                          confidence: float = 1.0,
                          metadata: Optional[Dict[str, Any]] = None,
                          expires_at: Optional[datetime] = None) -> str:
        """
        Store memory with event sourcing
        
        Args:
            memory_id: Optional memory ID (generated if not provided)
            agent_id: Agent storing the memory
            user_id: Associated user
            memory_type: Type of memory
            content: Memory content
            confidence: Confidence score
            metadata: Additional metadata
            expires_at: Optional expiration
            
        Returns:
            Memory ID
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            memory_id = memory_id or str(uuid.uuid4())
            stream_id = str(uuid.uuid4())
            
            if isinstance(memory_type, str):
                memory_type = MemoryType(memory_type)
            
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Create event for audit trail
                    event_id = await self._append_event(
                        conn=conn,
                        stream_id=stream_id,
                        event_type=EventType.MEMORY_CREATED,
                        payload={
                            'memory_id': memory_id,
                            'agent_id': agent_id,
                            'user_id': user_id,
                            'memory_type': memory_type.value,
                            'content': content,
                            'confidence': confidence,
                            'metadata': metadata,
                            'expires_at': expires_at.isoformat() if expires_at else None
                        }
                    )
                    
                    # Store in projection table
                    await conn.execute("""
                        INSERT INTO agent_memories 
                        (memory_id, agent_id, user_id, memory_type, content, 
                         metadata, confidence, expires_at, source_event_id)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """, memory_id, agent_id, user_id, memory_type.value,
                        json.dumps(content), json.dumps(metadata or {}),
                        confidence, expires_at, event_id)
            
            # Emit WebSocket event
            if self.event_emitter:
                await self._emit_memory_event('memory_created', {
                    'memory_id': memory_id,
                    'agent_id': agent_id,
                    'user_id': user_id,
                    'memory_type': memory_type.value,
                    'confidence': confidence
                })
            
            logger.info(f"Stored memory {memory_id} in PostgreSQL tier")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    async def retrieve_memory(self, memory_id: str) -> Optional[PostgresMemoryItem]:
        """Retrieve a specific memory"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT memory_id, agent_id, user_id, memory_type, content,
                           metadata, confidence, created_at, updated_at, 
                           expires_at, is_deleted, source_event_id
                    FROM agent_memories
                    WHERE memory_id = $1 AND NOT is_deleted
                """, memory_id)
                
                if not row:
                    return None
                
                # Record retrieval event
                await self._append_event(
                    conn=conn,
                    stream_id=str(uuid.uuid4()),
                    event_type=EventType.MEMORY_RETRIEVED,
                    payload={'memory_id': memory_id}
                )
                
                return PostgresMemoryItem(
                    memory_id=row['memory_id'],
                    agent_id=row['agent_id'],
                    user_id=row['user_id'],
                    memory_type=MemoryType(row['memory_type']),
                    content=json.loads(row['content']),
                    confidence=row['confidence'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    metadata=json.loads(row['metadata']),
                    source_event_id=row['source_event_id'],
                    expires_at=row['expires_at'],
                    is_deleted=row['is_deleted']
                )
                
        except Exception as e:
            logger.error(f"Failed to retrieve memory {memory_id}: {e}")
            return None
    
    async def get_user_memories(self,
                               user_id: str,
                               agent_id: Optional[str] = None,
                               memory_type: Optional[Union[str, MemoryType]] = None,
                               limit: int = 100,
                               offset: int = 0,
                               include_expired: bool = False) -> List[PostgresMemoryItem]:
        """Get memories for a user with filtering"""
        if not self._initialized:
            await self.initialize()
        
        try:
            conditions = ["user_id = $1", "NOT is_deleted"]
            params = [user_id]
            param_count = 1
            
            if agent_id:
                param_count += 1
                conditions.append(f"agent_id = ${param_count}")
                params.append(agent_id)
            
            if memory_type:
                param_count += 1
                if isinstance(memory_type, MemoryType):
                    memory_type = memory_type.value
                conditions.append(f"memory_type = ${param_count}")
                params.append(memory_type)
            
            if not include_expired:
                conditions.append("(expires_at IS NULL OR expires_at > NOW())")
            
            query = f"""
                SELECT memory_id, agent_id, user_id, memory_type, content,
                       metadata, confidence, created_at, updated_at,
                       expires_at, is_deleted, source_event_id
                FROM agent_memories
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                
                memories = []
                for row in rows:
                    memories.append(PostgresMemoryItem(
                        memory_id=row['memory_id'],
                        agent_id=row['agent_id'],
                        user_id=row['user_id'],
                        memory_type=MemoryType(row['memory_type']),
                        content=json.loads(row['content']),
                        confidence=row['confidence'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        metadata=json.loads(row['metadata']),
                        source_event_id=row['source_event_id'],
                        expires_at=row['expires_at'],
                        is_deleted=row['is_deleted']
                    ))
                
                return memories
                
        except Exception as e:
            logger.error(f"Failed to get user memories: {e}")
            return []
    
    async def update_memory(self,
                           memory_id: str,
                           content: Optional[Dict[str, Any]] = None,
                           metadata: Optional[Dict[str, Any]] = None,
                           confidence: Optional[float] = None) -> bool:
        """Update existing memory with event recording"""
        if not self._initialized:
            await self.initialize()
        
        try:
            updates = []
            params = []
            param_count = 0
            
            if content is not None:
                param_count += 1
                updates.append(f"content = ${param_count}")
                params.append(json.dumps(content))
            
            if metadata is not None:
                param_count += 1
                updates.append(f"metadata = ${param_count}")
                params.append(json.dumps(metadata))
            
            if confidence is not None:
                param_count += 1
                updates.append(f"confidence = ${param_count}")
                params.append(confidence)
            
            if not updates:
                return False
            
            param_count += 1
            query = f"""
                UPDATE agent_memories
                SET {', '.join(updates)}, updated_at = NOW()
                WHERE memory_id = ${param_count} AND NOT is_deleted
                RETURNING agent_id, user_id
            """
            params.append(memory_id)
            
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    row = await conn.fetchrow(query, *params)
                    
                    if not row:
                        return False
                    
                    # Record update event
                    await self._append_event(
                        conn=conn,
                        stream_id=str(uuid.uuid4()),
                        event_type=EventType.MEMORY_UPDATED,
                        payload={
                            'memory_id': memory_id,
                            'updates': {
                                'content': content,
                                'metadata': metadata,
                                'confidence': confidence
                            }
                        }
                    )
            
            # Emit WebSocket event
            if self.event_emitter:
                await self._emit_memory_event('memory_updated', {
                    'memory_id': memory_id,
                    'agent_id': row['agent_id'],
                    'user_id': row['user_id']
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Soft delete memory"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    row = await conn.fetchrow("""
                        UPDATE agent_memories
                        SET is_deleted = TRUE, updated_at = NOW()
                        WHERE memory_id = $1 AND NOT is_deleted
                        RETURNING agent_id, user_id
                    """, memory_id)
                    
                    if not row:
                        return False
                    
                    # Record deletion event
                    await self._append_event(
                        conn=conn,
                        stream_id=str(uuid.uuid4()),
                        event_type=EventType.MEMORY_DELETED,
                        payload={'memory_id': memory_id}
                    )
            
            # Emit WebSocket event
            if self.event_emitter:
                await self._emit_memory_event('memory_deleted', {
                    'memory_id': memory_id,
                    'agent_id': row['agent_id'],
                    'user_id': row['user_id']
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False
    
    async def search_memories(self,
                             query: str,
                             user_id: Optional[str] = None,
                             agent_id: Optional[str] = None,
                             limit: int = 50) -> List[PostgresMemoryItem]:
        """Full-text search across memories"""
        if not self._initialized:
            await self.initialize()
        
        try:
            conditions = ["NOT is_deleted"]
            params = [query]
            param_count = 1
            
            if user_id:
                param_count += 1
                conditions.append(f"user_id = ${param_count}")
                params.append(user_id)
            
            if agent_id:
                param_count += 1
                conditions.append(f"agent_id = ${param_count}")
                params.append(agent_id)
            
            # Use PostgreSQL full-text search
            search_query = f"""
                SELECT memory_id, agent_id, user_id, memory_type, content,
                       metadata, confidence, created_at, updated_at,
                       expires_at, is_deleted, source_event_id,
                       ts_rank(to_tsvector('english', content::text), 
                              plainto_tsquery('english', $1)) as relevance
                FROM agent_memories
                WHERE {' AND '.join(conditions)}
                AND to_tsvector('english', content::text) @@ plainto_tsquery('english', $1)
                ORDER BY relevance DESC, created_at DESC
                LIMIT ${param_count + 1}
            """
            params.append(limit)
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(search_query, *params)
                
                memories = []
                for row in rows:
                    memory = PostgresMemoryItem(
                        memory_id=row['memory_id'],
                        agent_id=row['agent_id'],
                        user_id=row['user_id'],
                        memory_type=MemoryType(row['memory_type']),
                        content=json.loads(row['content']),
                        confidence=row['confidence'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        metadata=json.loads(row['metadata']),
                        source_event_id=row['source_event_id'],
                        expires_at=row['expires_at'],
                        is_deleted=row['is_deleted']
                    )
                    # Add relevance score to metadata
                    memory.metadata['search_relevance'] = float(row['relevance'])
                    memories.append(memory)
                
                return memories
                
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    async def get_memory_stats(self, 
                              user_id: Optional[str] = None,
                              agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get memory statistics"""
        if not self._initialized:
            await self.initialize()
        
        try:
            conditions = ["NOT is_deleted"]
            params = []
            param_count = 0
            
            if user_id:
                param_count += 1
                conditions.append(f"user_id = ${param_count}")
                params.append(user_id)
            
            if agent_id:
                param_count += 1
                conditions.append(f"agent_id = ${param_count}")
                params.append(agent_id)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            query = f"""
                SELECT 
                    COUNT(*) as total_memories,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT agent_id) as unique_agents,
                    COUNT(*) FILTER (WHERE memory_type = 'fact') as facts,
                    COUNT(*) FILTER (WHERE memory_type = 'analysis') as analyses,
                    COUNT(*) FILTER (WHERE memory_type = 'recommendation') as recommendations,
                    AVG(confidence) as avg_confidence,
                    MAX(created_at) as latest_memory
                FROM agent_memories
                {where_clause}
            """
            
            async with self.pool.acquire() as conn:
                stats = await conn.fetchrow(query, *params)
                
                return {
                    'total_memories': stats['total_memories'],
                    'unique_users': stats['unique_users'],
                    'unique_agents': stats['unique_agents'],
                    'memory_breakdown': {
                        'facts': stats['facts'],
                        'analyses': stats['analyses'],
                        'recommendations': stats['recommendations']
                    },
                    'average_confidence': float(stats['avg_confidence'] or 0),
                    'latest_memory': stats['latest_memory'].isoformat() if stats['latest_memory'] else None,
                    'user_id': user_id,
                    'agent_id': agent_id
                }
                
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    async def promote_from_redis(self, memory_data: Dict[str, Any]) -> str:
        """Promote memory from Redis tier to PostgreSQL"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Extract data from Redis format
            memory_id = await self.store_memory(
                memory_id=memory_data.get('memory_id'),
                agent_id=memory_data['agent_id'],
                user_id=memory_data['user_id'],
                memory_type=memory_data['memory_type'],
                content=memory_data['content'],
                confidence=memory_data.get('confidence', 1.0),
                metadata={
                    **memory_data.get('metadata', {}),
                    'promoted_from': 'redis',
                    'original_created_at': memory_data.get('created_at'),
                    'access_count': memory_data.get('access_count', 0)
                }
            )
            
            # Record promotion event
            async with self.pool.acquire() as conn:
                await self._append_event(
                    conn=conn,
                    stream_id=str(uuid.uuid4()),
                    event_type=EventType.MEMORY_PROMOTED,
                    payload={
                        'memory_id': memory_id,
                        'from_tier': 'redis',
                        'to_tier': 'postgresql'
                    }
                )
            
            logger.info(f"Promoted memory {memory_id} from Redis to PostgreSQL")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to promote memory from Redis: {e}")
            raise
    
    async def _append_event(self,
                           conn: asyncpg.Connection,
                           stream_id: str,
                           event_type: EventType,
                           payload: Dict[str, Any],
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """Append event to event store"""
        try:
            event_id = str(uuid.uuid4())
            metadata = metadata or {}
            metadata['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Get current version for stream
            current_version = await conn.fetchval(
                "SELECT COALESCE(MAX(version), 0) FROM events WHERE stream_id = $1",
                stream_id
            ) or 0
            
            new_version = current_version + 1
            
            # Insert event
            await conn.execute("""
                INSERT INTO events 
                (event_id, stream_id, event_type, version, payload, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, event_id, stream_id, event_type.value, new_version,
                json.dumps(payload), json.dumps(metadata))
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to append event: {e}")
            raise
    
    async def _emit_memory_event(self, event_type: str, data: Dict[str, Any]):
        """Emit memory event for dashboard"""
        if self.event_emitter:
            try:
                await self.event_emitter.emit({
                    'type': f'postgres_tier_{event_type}',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'data': data
                })
            except Exception as e:
                logger.error(f"Failed to emit event: {e}")
    
    async def cleanup_expired(self) -> int:
        """Clean up expired memories"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE agent_memories
                    SET is_deleted = TRUE, updated_at = NOW()
                    WHERE expires_at < NOW() AND NOT is_deleted
                """)
                
                deleted_count = int(result.split()[-1])
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired memories")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired memories: {e}")
            return 0
    
    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL tier connection closed")
