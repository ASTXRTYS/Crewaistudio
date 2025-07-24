"""
PostgreSQL Memory Backend for Specialist Agents
This replaces the limited JSON file storage with scalable database storage
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncpg
from asyncpg.pool import Pool

class PostgreSQLMemoryBackend:
    """
    Scalable memory backend for specialist agents using PostgreSQL.
    
    This implementation supports:
    - Unlimited hypothesis storage (vs 1000 record limit)
    - Concurrent access from multiple agents
    - Full ACID guarantees for data integrity
    - Efficient querying and filtering
    - Proper versioning and history tracking
    """
    
    def __init__(self, 
                 pool: Pool,
                 specialist_type: str,
                 user_id: Optional[str] = None):
        """
        Initialize the PostgreSQL memory backend.
        
        Args:
            pool: asyncpg connection pool (shared across application)
            specialist_type: Type of specialist (neuroscientist, nutritionist, etc.)
            user_id: Optional user ID for user-specific memory isolation
        """
        self.pool = pool
        self.specialist_type = specialist_type
        self.user_id = user_id
        self._initialized = False
    
    async def initialize(self):
        """
        Ensure database tables exist for this specialist's memory.
        This is idempotent - safe to call multiple times.
        """
        async with self.pool.acquire() as conn:
            # Create specialist memory table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS specialist_memory (
                    id SERIAL PRIMARY KEY,
                    specialist_type VARCHAR(50) NOT NULL,
                    user_id VARCHAR(255),
                    memory_type VARCHAR(50) NOT NULL,
                    content JSONB NOT NULL,
                    confidence_score FLOAT DEFAULT 0.5,
                    validation_status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    version INTEGER DEFAULT 1,
                    parent_id INTEGER REFERENCES specialist_memory(id),
                    metadata JSONB DEFAULT '{}',
                    
                    -- Indexes for performance
                    INDEX idx_specialist_user (specialist_type, user_id),
                    INDEX idx_memory_type (memory_type),
                    INDEX idx_created_at (created_at DESC),
                    INDEX idx_validation_status (validation_status)
                );
            """)
            
            # Create hypothesis tracking table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS specialist_hypotheses (
                    id SERIAL PRIMARY KEY,
                    specialist_type VARCHAR(50) NOT NULL,
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
                    
                    INDEX idx_hypothesis_specialist (specialist_type, user_id),
                    INDEX idx_hypothesis_status (status),
                    INDEX idx_confidence_delta (current_confidence - initial_confidence)
                );
            """)
            
            # Create trigger for updated_at
            await conn.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                
                CREATE TRIGGER update_specialist_memory_updated_at 
                    BEFORE UPDATE ON specialist_memory 
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """)
            
            self._initialized = True
    
    async def add_memory(self, 
                        memory_type: str, 
                        content: Dict[str, Any],
                        confidence: float = 0.5) -> int:
        """
        Add a new memory entry for this specialist.
        
        Args:
            memory_type: Type of memory (observation, insight, pattern, etc.)
            content: The actual memory content as a dictionary
            confidence: Initial confidence score (0.0 to 1.0)
            
        Returns:
            The ID of the created memory entry
        """
        if not self._initialized:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            memory_id = await conn.fetchval("""
                INSERT INTO specialist_memory 
                (specialist_type, user_id, memory_type, content, confidence_score)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, self.specialist_type, self.user_id, memory_type, 
                json.dumps(content), confidence)
            
            return memory_id
    
    async def get_memories(self,
                          memory_type: Optional[str] = None,
                          limit: int = 100,
                          offset: int = 0,
                          min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        Retrieve memories for this specialist with filtering options.
        
        This replaces the limited JSON loading with powerful database queries.
        """
        if not self._initialized:
            await self.initialize()
            
        query = """
            SELECT id, memory_type, content, confidence_score, 
                   validation_status, created_at, updated_at, metadata
            FROM specialist_memory
            WHERE specialist_type = $1
              AND ($2::VARCHAR IS NULL OR user_id = $2)
              AND ($3::VARCHAR IS NULL OR memory_type = $3)
              AND confidence_score >= $4
            ORDER BY created_at DESC
            LIMIT $5 OFFSET $6
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                query, self.specialist_type, self.user_id, 
                memory_type, min_confidence, limit, offset
            )
            
            return [dict(row) for row in rows]
    
    async def add_hypothesis(self,
                           hypothesis: str,
                           initial_confidence: float) -> int:
        """
        Create a new hypothesis that the specialist will track and validate.
        
        This is crucial for the learning system - agents must be able to
        form hypotheses and track their accuracy over time.
        """
        if not self._initialized:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            hypothesis_id = await conn.fetchval("""
                INSERT INTO specialist_hypotheses
                (specialist_type, user_id, hypothesis_text, 
                 initial_confidence, current_confidence)
                VALUES ($1, $2, $3, $4, $4)
                RETURNING id
            """, self.specialist_type, self.user_id, hypothesis, initial_confidence)
            
            return hypothesis_id
    
    async def update_hypothesis(self,
                              hypothesis_id: int,
                              test_result: Dict[str, Any],
                              new_confidence: float):
        """
        Update a hypothesis based on new evidence.
        
        This is how specialists learn from their mistakes and successes.
        """
        async with self.pool.acquire() as conn:
            # Get current hypothesis data
            current = await conn.fetchrow("""
                SELECT evidence_for, evidence_against, test_count, 
                       validation_outcomes
                FROM specialist_hypotheses
                WHERE id = $1 AND specialist_type = $2
            """, hypothesis_id, self.specialist_type)
            
            if not current:
                raise ValueError(f"Hypothesis {hypothesis_id} not found")
            
            # Determine if this is supporting or contradicting evidence
            if test_result.get('supports_hypothesis', False):
                evidence_for = json.loads(current['evidence_for'])
                evidence_for.append(test_result)
                evidence_against = current['evidence_against']
            else:
                evidence_against = json.loads(current['evidence_against'])
                evidence_against.append(test_result)
                evidence_for = current['evidence_for']
            
            # Add to validation outcomes
            outcomes = json.loads(current['validation_outcomes'])
            outcomes.append({
                'timestamp': datetime.utcnow().isoformat(),
                'result': test_result,
                'confidence_change': new_confidence - current['current_confidence']
            })
            
            # Update the hypothesis
            await conn.execute("""
                UPDATE specialist_hypotheses
                SET current_confidence = $1,
                    evidence_for = $2,
                    evidence_against = $3,
                    test_count = test_count + 1,
                    last_tested_at = NOW(),
                    validation_outcomes = $4,
                    status = CASE 
                        WHEN $1 < 0.2 THEN 'rejected'
                        WHEN $1 > 0.8 THEN 'validated'
                        ELSE 'active'
                    END
                WHERE id = $5
            """, new_confidence, json.dumps(evidence_for), 
                json.dumps(evidence_against), json.dumps(outcomes), 
                hypothesis_id)
    
    async def get_learning_history(self) -> Dict[str, Any]:
        """
        Retrieve the specialist's complete learning history.
        
        This shows how the specialist has evolved and learned over time.
        """
        async with self.pool.acquire() as conn:
            # Get hypothesis performance
            hypotheses = await conn.fetch("""
                SELECT hypothesis_text, initial_confidence, current_confidence,
                       status, test_count, created_at, last_tested_at,
                       (current_confidence - initial_confidence) as confidence_delta
                FROM specialist_hypotheses
                WHERE specialist_type = $1 
                  AND ($2::VARCHAR IS NULL OR user_id = $2)
                ORDER BY ABS(current_confidence - initial_confidence) DESC
            """, self.specialist_type, self.user_id)
            
            # Get memory evolution
            memory_stats = await conn.fetchrow("""
                SELECT COUNT(*) as total_memories,
                       AVG(confidence_score) as avg_confidence,
                       COUNT(DISTINCT memory_type) as memory_types,
                       MIN(created_at) as earliest_memory,
                       MAX(created_at) as latest_memory
                FROM specialist_memory
                WHERE specialist_type = $1
                  AND ($2::VARCHAR IS NULL OR user_id = $2)
            """, self.specialist_type, self.user_id)
            
            return {
                'hypotheses': [dict(h) for h in hypotheses],
                'memory_statistics': dict(memory_stats),
                'learning_rate': self._calculate_learning_rate(hypotheses)
            }
    
    def _calculate_learning_rate(self, hypotheses) -> float:
        """
        Calculate how effectively this specialist is learning.
        
        A higher rate indicates the specialist is getting better at
        forming accurate hypotheses over time.
        """
        if not hypotheses:
            return 0.0
            
        # Calculate based on how confidence predictions match outcomes
        total_delta = sum(abs(h['confidence_delta']) for h in hypotheses)
        validated_count = sum(1 for h in hypotheses if h['status'] == 'validated')
        
        if len(hypotheses) == 0:
            return 0.0
            
        return (validated_count / len(hypotheses)) * (1 - (total_delta / len(hypotheses)))
    
    async def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of memory usage for monitoring."""
        async with self.pool.acquire() as conn:
            summary = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_memories,
                    COUNT(DISTINCT memory_type) as memory_types,
                    AVG(confidence_score) as avg_confidence,
                    MAX(created_at) as latest_memory,
                    MIN(created_at) as earliest_memory
                FROM specialist_memory
                WHERE specialist_type = $1
                  AND ($2::VARCHAR IS NULL OR user_id = $2)
            """, self.specialist_type, self.user_id)
            
            hypothesis_summary = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_hypotheses,
                    COUNT(*) FILTER (WHERE status = 'validated') as validated,
                    COUNT(*) FILTER (WHERE status = 'rejected') as rejected,
                    AVG(current_confidence) as avg_confidence
                FROM specialist_hypotheses
                WHERE specialist_type = $1
                  AND ($2::VARCHAR IS NULL OR user_id = $2)
            """, self.specialist_type, self.user_id)
            
            return {
                'memory': dict(summary),
                'hypotheses': dict(hypothesis_summary),
                'specialist_type': self.specialist_type,
                'user_id': self.user_id
            }
