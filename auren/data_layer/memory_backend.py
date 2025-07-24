"""
PostgreSQL Memory Backend for AUREN Intelligence System

Provides persistent storage for agent knowledge using PostgreSQL.
Replaces the limited JSON file storage with scalable database storage.

Key Features:
- Unlimited storage capacity (vs 1000 record limit)
- Concurrent access from multiple agents
- Full ACID guarantees for data integrity
- Efficient querying and filtering
- Proper versioning and history tracking
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import asyncpg
from asyncpg.pool import Pool
import logging

logger = logging.getLogger(__name__)


class PostgreSQLMemoryBackend:
    """
    Scalable memory backend for specialist agents using PostgreSQL.
    
    This implementation supports:
    - Unlimited hypothesis storage (vs 1000 record limit)
    - Concurrent access from multiple agents
    - Full ACID guarantees for data integrity
    - Efficient querying and filtering
    - Proper versioning and history tracking
    
    Example:
        >>> backend = PostgreSQLMemoryBackend(pool, "neuroscientist", "user123")
        >>> await backend.store("knowledge", {"insight": "test"}, 0.9)
        >>> memories = await backend.retrieve(limit=10)
    """
    
    def __init__(self, 
                 pool: Pool,
                 agent_type: str,
                 user_id: Optional[str] = None):
        """
        Initialize the PostgreSQL memory backend.
        
        Args:
            pool: asyncpg connection pool (shared across application)
            agent_type: Type of specialist (neuroscientist, nutritionist, etc.)
            user_id: Optional user ID for user-specific memory isolation
        """
        self.pool = pool
        self.agent_type = agent_type
        self.user_id = user_id
        self._initialized = False
    
    async def initialize(self):
        """
        Ensure database tables exist for this agent's memory.
        This is idempotent - safe to call multiple times.
        """
        if self._initialized:
            return
            
        async with self.pool.acquire() as conn:
            # Create agent memory table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_memory (
                    id SERIAL PRIMARY KEY,
                    agent_type VARCHAR(50) NOT NULL,
                    user_id VARCHAR(255),
                    memory_type VARCHAR(50) NOT NULL,
                    content JSONB NOT NULL,
                    confidence_score FLOAT DEFAULT 0.5,
                    validation_status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    version INTEGER DEFAULT 1,
                    parent_id INTEGER REFERENCES agent_memory(id),
                    metadata JSONB DEFAULT '{}',
                    
                    INDEX idx_agent_user (agent_type, user_id),
                    INDEX idx_memory_type (memory_type),
                    INDEX idx_created_at (created_at DESC),
                    INDEX idx_validation_status (validation_status)
                );
            """)
            
            # Create hypothesis tracking table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_hypotheses (
                    id SERIAL PRIMARY KEY,
                    agent_type VARCHAR(50) NOT NULL,
                    user_id VARCHAR(255),
                    hypothesis_text TEXT NOT NULL,
                    initial_confidence FLOAT NOT NULL,
                    current_confidence FLOAT NOT NULL,
                    evidence_for JSONB DEFAULT '[]',
                    evidence_against JSONB DEFAULT '[]',
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    last_tested_at TIMESTAMPTZ,
                    test_count INTEGER DEFAULT 0,
                    validation_outcomes JSONB DEFAULT '[]',
                    
                    INDEX idx_hypothesis_agent (agent_type, user_id),
                    INDEX idx_hypothesis_status (status),
                    INDEX idx_confidence_delta (current_confidence - initial_confidence)
                );
            """)
            
            self._initialized = True
            logger.info(f"PostgreSQL memory backend initialized for {self.agent_type}")
    
    async def store(self, 
                   memory_type: str, 
                   content: Dict[str, Any],
                   confidence: float = 0.5,
                   metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Store a new memory entry for this agent.
        
        Args:
            memory_type: Type of memory (observation, insight, pattern, etc.)
            content: The actual memory content as a dictionary
            confidence: Initial confidence score (0.0 to 1.0)
            metadata: Additional metadata for the memory
            
        Returns:
            The ID of the created memory entry
        """
        if not self._initialized:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            memory_id = await conn.fetchval("""
                INSERT INTO agent_memory 
                (agent_type, user_id, memory_type, content, confidence_score, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, self.agent_type, self.user_id, memory_type, 
                json.dumps(content), confidence, json.dumps(metadata or {}))
            
            logger.debug(f"Stored memory {memory_id} for {self.agent_type}")
            return memory_id
    
    async def retrieve(self,
                      memory_type: Optional[str] = None,
                      limit: int = 100,
                      offset: int = 0,
                      min_confidence: float = 0.0,
                      order_by: str = "created_at") -> List[Dict[str, Any]]:
        """
        Retrieve memories for this agent with filtering options.
        
        Args:
            memory_type: Filter by memory type
            limit: Maximum number of records to return
            offset: Number of records to skip
            min_confidence: Minimum confidence score
            order_by: Field to order by
            
        Returns:
            List of memory dictionaries
        """
        if not self._initialized:
            await self.initialize()
            
        query = """
            SELECT id, memory_type, content, confidence_score, 
                   validation_status, created_at, updated_at, metadata
            FROM agent_memory
            WHERE agent_type = $1
              AND ($2::VARCHAR IS NULL OR user_id = $2)
              AND ($3::VARCHAR IS NULL OR memory_type = $3)
              AND confidence_score >= $4
            ORDER BY created_at DESC
            LIMIT $5 OFFSET $6
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                query, self.agent_type, self.user_id, 
                memory_type, min_confidence, limit, offset
            )
            
            memories = []
            for row in rows:
                memory = dict(row)
                memory['content'] = json.loads(memory['content']) if isinstance(memory['content'], str) else memory['content']
                memory['metadata'] = json.loads(memory['metadata']) if isinstance(memory['metadata'], str) else memory['metadata']
                memories.append(memory)
            
            return memories
    
    async def store_hypothesis(self,
                             hypothesis: str,
                             initial_confidence: float,
                             metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Create a new hypothesis that the agent will track and validate.
        
        Args:
            hypothesis: The hypothesis text
            initial_confidence: Initial confidence in the hypothesis (0-1)
            metadata: Additional context for the hypothesis
            
        Returns:
            The ID of the created hypothesis
        """
        if not self._initialized:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            hypothesis_id = await conn.fetchval("""
                INSERT INTO agent_hypotheses
                (agent_type, user_id, hypothesis_text, 
                 initial_confidence, current_confidence, metadata)
                VALUES ($1, $2, $3, $4, $4, $5)
                RETURNING id
            """, self.agent_type, self.user_id, hypothesis, initial_confidence,
                json.dumps(metadata or {}))
            
            logger.debug(f"Created hypothesis {hypothesis_id}: {hypothesis[:50]}...")
            return hypothesis_id
    
    async def update_hypothesis(self,
                              hypothesis_id: int,
                              new_confidence: float,
                              evidence: Optional[Dict[str, Any]] = None):
        """
        Update a hypothesis based on new evidence.
        
        Args:
            hypothesis_id: ID of the hypothesis to update
            new_confidence: Updated confidence score
            evidence: New evidence supporting or contradicting the hypothesis
        """
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE agent_hypotheses
                SET current_confidence = $1,
                    last_tested_at = NOW(),
                    test_count = test_count + 1,
                    status = CASE 
                        WHEN $1 < 0.2 THEN 'rejected'
                        WHEN $1 > 0.8 THEN 'validated'
                        ELSE 'active'
                    END
                WHERE id = $2 AND agent_type = $3
            """, new_confidence, hypothesis_id, self.agent_type)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory statistics for this agent.
        
        Returns:
            Dictionary with memory statistics
        """
        if not self._initialized:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_memories,
                    AVG(confidence_score) as avg_confidence,
                    COUNT(DISTINCT memory_type) as memory_types,
                    MIN(created_at) as earliest_memory,
                    MAX(created_at) as latest_memory,
                    COUNT(*) FILTER (WHERE validation_status = 'validated') as validated_memories
                FROM agent_memory
                WHERE agent_type = $1
                  AND ($2::VARCHAR IS NULL OR user_id = $2)
            """, self.agent_type, self.user_id)
            
            return dict(stats) if stats else {}


def create_memory_backend(pool: Pool, agent_type: str, user_id: Optional[str] = None) -> PostgreSQLMemoryBackend:
    """
    Factory function to create a PostgreSQLMemoryBackend instance.
    
    Args:
        pool: Database connection pool
        agent_type: Type of agent
        user_id: Optional user ID
        
    Returns:
        Configured PostgreSQLMemoryBackend instance
    """
    return PostgreSQLMemoryBackend(pool, agent_type, user_id)
