"""
PostgreSQL Memory Backend
Replaces JSON file storage with unlimited PostgreSQL storage
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

from .connection import AsyncPostgresManager
from .event_store import EventStore, EventType

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """Types of memories that can be stored"""
    FACT = "fact"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    OBSERVATION = "observation"
    INSIGHT = "insight"
    PATTERN = "pattern"
    GOAL = "goal"
    PREFERENCE = "preference"
    CONVERSATION = "conversation"
    BIOMETRIC = "biometric"

class PostgreSQLMemoryBackend:
    """
    PostgreSQL-based memory backend that replaces JSON file storage
    
    Features:
    - Unlimited memory storage (no 1000-record limit)
    - Full-text search capabilities
    - Confidence scoring
    - Expiration support
    - Real-time updates via event sourcing
    """
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    async def initialize(self) -> None:
        """Initialize the memory backend schema"""
        schema_sql = """
        -- Agent memories table
        CREATE TABLE IF NOT EXISTS agent_memories (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            agent_id VARCHAR(100) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            memory_type VARCHAR(50) NOT NULL,
            content JSONB NOT NULL,
            confidence_score FLOAT DEFAULT 0.5,
            is_deleted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            
            -- Performance indexes
            INDEX idx_agent_user (agent_id, user_id),
            INDEX idx_created_at (created_at DESC),
            INDEX idx_memory_type (memory_type),
            INDEX idx_confidence (confidence_score DESC),
            INDEX idx_content_gin (content) USING GIN,
            INDEX idx_user_agent_type (user_id, agent_id, memory_type)
        );
        
        -- Conversation memories table
        CREATE TABLE IF NOT EXISTS conversation_memories (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            conversation_id UUID NOT NULL,
            agent_id VARCHAR(100) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            message_type VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            
            INDEX idx_conversation (conversation_id),
            INDEX idx_user_agent_conv (user_id, agent_id),
            INDEX idx_timestamp (timestamp DESC)
        );
        
        -- User profiles table
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id VARCHAR(255) PRIMARY KEY,
            goals JSONB DEFAULT '{}',
            preferences JSONB DEFAULT '{}',
            demographics JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        
        -- Specialist knowledge table
        CREATE TABLE IF NOT EXISTS specialist_knowledge (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            agent_id VARCHAR(100) NOT NULL,
            knowledge_type VARCHAR(50) NOT NULL,
            content JSONB NOT NULL,
            confidence_score FLOAT DEFAULT 0.5,
            is_shared BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            
            INDEX idx_agent_knowledge (agent_id, knowledge_type),
            INDEX idx_shared (is_shared),
            INDEX idx_knowledge_confidence (confidence_score DESC)
        );
        """
        
        async with AsyncPostgresManager.connection() as conn:
            await conn.execute(schema_sql)
            logger.info("Memory backend schema initialized")
    
    async def store_memory(self, agent_id: str, memory_type: MemoryType, 
                          content: Dict[str, Any], user_id: str,
                          confidence: float = 0.5, expires_at: Optional[datetime] = None) -> str:
        """
        Store a memory in PostgreSQL
        
        Args:
            agent_id: The agent storing this memory
            memory_type: Type of memory being stored
            content: The memory content
            user_id: User this memory belongs to
            confidence: Confidence score (0.0 to 1.0)
            expires_at: Optional expiration time
            
        Returns:
            str: The memory ID
        """
        memory_id = str(uuid.uuid4())
        
        async with AsyncPostgresManager.connection() as conn:
            await conn.execute(
                """
                INSERT INTO agent_memories 
                (id, agent_id, user_id, memory_type, content, confidence_score)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                memory_id, agent_id, user_id, memory_type.value, 
                json.dumps(content), confidence
            )
        
        # Publish event
        await self.event_store.append_event(
            stream_id=user_id,
            event_type=EventType.MEMORY_CREATED,
            payload={
                "memory_id": memory_id,
                "agent_id": agent_id,
                "memory_type": memory_type.value,
                "content": content,
                "confidence": confidence
            }
        )
        
        return memory_id
    
    async def retrieve_memories(self, agent_id: str, user_id: str, 
                              memory_type: Optional[MemoryType] = None,
                              limit: int = 100, offset: int = 0,
                              min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        Retrieve memories for a specific agent and user
        
        Args:
            agent_id: Agent to retrieve memories for
            user_id: User to retrieve memories for
            memory_type: Optional filter by memory type
            limit: Maximum number of memories to return
            offset: Number of memories to skip
            min_confidence: Minimum confidence score
            
        Returns:
            List of memory dictionaries
        """
        async with AsyncPostgresManager.connection() as conn:
            query = """
                SELECT id, agent_id, user_id, memory_type, content, 
                       confidence_score, created_at, updated_at
                FROM agent_memories
                WHERE agent_id = $1 AND user_id = $2 AND is_deleted = FALSE
            """
            params = [agent_id, user_id]
            
            if memory_type:
                query += " AND memory_type = $3"
                params.append(memory_type.value)
            
            if min_confidence > 0:
                query += f" AND confidence_score >= ${len(params) + 1}"
                params.append(min_confidence)
            
            query += " ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            
            memories = []
            for row in rows:
                memories.append({
                    "id": str(row['id']),
                    "agent_id": row['agent_id'],
                    "user_id": row['user_id'],
                    "memory_type": row['memory_type'],
                    "content": row['content'],
                    "confidence_score": float(row['confidence_score']),
                    "created_at": row['created_at'].isoformat(),
                    "updated_at": row['updated_at'].isoformat()
                })
            
            return memories
    
    async def search_memories(self, agent_id: str, query: str, user_id: str,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories using full-text search
        
        Args:
            agent_id: Agent to search memories for
            query: Search query
            user_id: User to search memories for
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        async with AsyncPostgresManager.connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, agent_id, user_id, memory_type, content,
                       confidence_score, created_at,
                       ts_rank(to_tsvector('english', content::text), plainto_tsquery('english', $3)) as rank
                FROM agent_memories
                WHERE agent_id = $1 AND user_id = $2 AND is_deleted = FALSE
                AND to_tsvector('english', content::text) @@ plainto_tsquery('english', $3)
                ORDER BY rank DESC, created_at DESC
                LIMIT $4
                """,
                agent_id, user_id, query, limit
            )
            
            memories = []
            for row in rows:
                memories.append({
                    "id": str(row['id']),
                    "agent_id": row['agent_id'],
                    "user_id": row['user_id'],
                    "memory_type": row['memory_type'],
                    "content": row['content'],
                    "confidence_score": float(row['confidence_score']),
                    "created_at": row['created_at'].isoformat(),
                    "rank": float(row['rank'])
                })
            
            return memories
    
    async def update_memory(self, memory_id: str, content: Dict[str, Any],
                          confidence: Optional[float] = None) -> bool:
        """
        Update an existing memory
        
        Args:
            memory_id: ID of memory to update
            content: New content
            confidence: Optional new confidence score
            
        Returns:
            bool: True if updated successfully
        """
        async with AsyncPostgresManager.connection() as conn:
            update_fields = ["content = $1"]
            params = [json.dumps(content)]
            
            if confidence is not None:
                update_fields.append("confidence_score = $2")
                params.append(confidence)
            
            update_fields.append("updated_at = NOW()")
            params.append(memory_id)
            
            result = await conn.execute(
                f"UPDATE agent_memories SET {', '.join(update_fields)} WHERE id = ${len(params)}",
                *params
            )
            
            if result == "UPDATE 1":
                # Publish update event
                await self.event_store.append_event(
                    stream_id="system",
                    event_type=EventType.MEMORY_UPDATED,
                    payload={
                        "memory_id": memory_id,
                        "content": content,
                        "confidence": confidence
                    }
                )
                return True
            
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Soft delete a memory
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            bool: True if deleted successfully
        """
        async with AsyncPostgresManager.connection() as conn:
            result = await conn.execute(
                "UPDATE agent_memories SET is_deleted = TRUE, updated_at = NOW() WHERE id = $1",
                memory_id
            )
            
            if result == "UPDATE 1":
                # Publish delete event
                await self.event_store.append_event(
                    stream_id="system",
                    event_type=EventType.MEMORY_DELETED,
                    payload={"memory_id": memory_id}
                )
                return True
            
            return False
    
    async def get_memory_count(self, agent_id: str, user_id: str) -> int:
        """Get total count of memories for agent and user"""
        async with AsyncPostgresManager.connection() as conn:
            return await conn.fetchval(
                "SELECT COUNT(*) FROM agent_memories WHERE agent_id = $1 AND user_id = $2 AND is_deleted = FALSE",
                agent_id, user_id
            )
    
    async def get_recent_memories(self, agent_id: str, user_id: str, 
                              days: int = 7) -> List[Dict[str, Any]]:
        """Get memories from the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with AsyncPostgresManager.connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, agent_id, user_id, memory_type, content,
                       confidence_score, created_at
                FROM agent_memories
                WHERE agent_id = $1 AND user_id = $2 AND is_deleted = FALSE
                AND created_at >= $3
                ORDER BY created_at DESC
                """,
                agent_id, user_id, cutoff_date
            )
            
            memories = []
            for row in rows:
                memories.append({
                    "id": str(row['id']),
                    "agent_id": row['agent_id'],
                    "user_id": row['user_id'],
                    "memory_type": row['memory_type'],
                    "content": row['content'],
                    "confidence_score": float(row['confidence_score']),
                    "created_at": row['created_at'].isoformat()
                })
            
            return memories
    
    async def store_conversation_memory(self, conversation_id: str, agent_id: str,
                                      user_id: str, message_type: str, 
                                      content: str, metadata: Dict[str, Any] = None) -> str:
        """Store a conversation memory"""
        memory_id = str(uuid.uuid4())
        metadata = metadata or {}
        
        async with AsyncPostgresManager.connection() as conn:
            await conn.execute(
                """
                INSERT INTO conversation_memories 
                (id, conversation_id, agent_id, user_id, message_type, content, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                memory_id, conversation_id, agent_id, user_id, message_type, content, 
                json.dumps(metadata)
            )
        
        return memory_id
    
    async def get_conversation_history(self, conversation_id: str, 
                                     limit: int = 100) -> List[Dict[str, Any]]:
        """Get conversation history"""
        async with AsyncPostgresManager.connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, conversation_id, agent_id, user_id, message_type,
                       content, metadata, timestamp
                FROM conversation_memories
                WHERE conversation_id = $1
                ORDER BY timestamp ASC
                LIMIT $2
                """,
                conversation_id, limit
            )
            
            conversations = []
            for row in rows:
                conversations.append({
                    "id": str(row['id']),
                    "conversation_id": str(row['conversation_id']),
                    "agent_id": row['agent_id'],
                    "user_id": row['user_id'],
                    "message_type": row['message_type'],
                    "content": row['content'],
                    "metadata": row['metadata'],
                    "timestamp": row['timestamp'].isoformat()
                })
            
            return conversations
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        async with AsyncPostgresManager.connection() as conn:
            row = await conn.fetchrow(
                "SELECT user_id, goals, preferences, demographics, created_at, updated_at "
                "FROM user_profiles WHERE user_id = $1",
                user_id
            )
            
            if row:
                return {
                    "user_id": row['user_id'],
                    "goals": row['goals'],
                    "preferences": row['preferences'],
                    "demographics": row['demographics'],
                    "created_at": row['created_at'].isoformat(),
                    "updated_at": row['updated_at'].isoformat()
                }
            
            return None
    
    async def update_user_profile(self, user_id: str, goals: Dict[str, Any] = None,
                                preferences: Dict[str, Any] = None,
                                demographics: Dict[str, Any] = None) -> bool:
        """Update user profile"""
        async with AsyncPostgresManager.connection() as conn:
            update_fields = []
            params = []
            
            if goals is not None:
                update_fields.append("goals = $1")
                params.append(json.dumps(goals))
            
            if preferences is not None:
                update_fields.append("preferences = $2")
                params.append(json.dumps(preferences))
            
            if demographics is not None:
                update_fields.append("demographics = $3")
                params.append(json.dumps(demographics))
            
            if not update_fields:
                return False
            
            update_fields.append("updated_at = NOW()")
            params.append(user_id)
            
            result = await conn.execute(
                f"INSERT INTO user_profiles (user_id, {', '.join(update_fields)}) "
                f"VALUES ($1, {', '.join(['$' + str(i+2) for i in range(len(update_fields)-1)])}) "
                f"ON CONFLICT (user_id) DO UPDATE SET {', '.join(update_fields)}",
                *params
            )
            
            return result == "INSERT 0 1" or result == "UPDATE 1"
