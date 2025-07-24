"""
Knowledge Management Service
Enables agents to organize, share, and evolve their knowledge
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
import asyncpg
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeItem:
    """Represents a piece of agent knowledge"""
    id: str
    category: str
    content: Dict[str, Any]
    confidence: float
    source_agent: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    version: int
    parent_id: Optional[str] = None
    shared_with: List[str] = None
    
    def __post_init__(self):
        if self.shared_with is None:
            self.shared_with = []

class KnowledgeManager:
    """
    Central service for agent knowledge management
    
    Features:
    - Hierarchical knowledge organization
    - Knowledge sharing between agents
    - Versioning and evolution tracking
    - Confidence-based prioritization
    - Cross-agent validation
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.pool = db_pool
        
    async def initialize(self):
        """Initialize knowledge management tables"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_knowledge (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    category VARCHAR(100) NOT NULL,
                    content JSONB NOT NULL,
                    confidence FLOAT DEFAULT 0.5,
                    source_agent VARCHAR(50) NOT NULL,
                    tags TEXT[] DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    version INTEGER DEFAULT 1,
                    parent_id UUID REFERENCES agent_knowledge(id),
                    shared_with TEXT[] DEFAULT '{}',
                    
                    INDEX idx_category (category),
                    INDEX idx_source_agent (source_agent),
                    INDEX idx_confidence (confidence DESC),
                    INDEX idx_tags (tags),
                    INDEX idx_created_at (created_at DESC)
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_relationships (
                    id SERIAL PRIMARY KEY,
                    source_knowledge_id UUID REFERENCES agent_knowledge(id),
                    target_knowledge_id UUID REFERENCES agent_knowledge(id),
                    relationship_type VARCHAR(50) NOT NULL,
                    strength FLOAT DEFAULT 1.0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    
                    UNIQUE(source_knowledge_id, target_knowledge_id, relationship_type),
                    INDEX idx_source_relationships (source_knowledge_id),
                    INDEX idx_target_relationships (target_knowledge_id)
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_validation (
                    id SERIAL PRIMARY KEY,
                    knowledge_id UUID REFERENCES agent_knowledge(id),
                    validator_agent VARCHAR(50) NOT NULL,
                    validation_type VARCHAR(50) NOT NULL,
                    validation_data JSONB NOT NULL,
                    confidence_change FLOAT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    
                    INDEX idx_knowledge_validation (knowledge_id),
                    INDEX idx_validator_agent (validator_agent)
                );
            """)
    
    async def add_knowledge(self,
                          category: str,
                          content: Dict[str, Any],
                          source_agent: str,
                          confidence: float = 0.5,
                          tags: Optional[List[str]] = None,
                          parent_id: Optional[str] = None) -> str:
        """Add new knowledge item"""
        
        if tags is None:
            tags = []
            
        async with self.pool.acquire() as conn:
            knowledge_id = await conn.fetchval("""
                INSERT INTO agent_knowledge
                (category, content, confidence, source_agent, tags, parent_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id::text
            """, category, json.dumps(content), confidence, source_agent, tags, parent_id)
            
            return knowledge_id
    
    async def get_knowledge(self,
                          category: Optional[str] = None,
                          source_agent: Optional[str] = None,
                          min_confidence: float = 0.0,
                          limit: int = 100) -> List[KnowledgeItem]:
        """Retrieve knowledge items with filtering"""
        
        query = """
            SELECT id::text, category, content, confidence, source_agent,
                   tags, created_at, updated_at, version, parent_id::text,
                   shared_with
            FROM agent_knowledge
            WHERE confidence >= $1
        """
        params = [min_confidence]
        
        if category:
            query += " AND category = $2"
            params.append(category)
            
        if source_agent:
            query += f" AND source_agent = ${len(params) + 1}"
            params.append(source_agent)
            
        query += " ORDER BY confidence DESC, created_at DESC LIMIT $2"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            return [
                KnowledgeItem(
                    id=row['id'],
                    category=row['category'],
                    content=row['content'],
                    confidence=row['confidence'],
                    source_agent=row['source_agent'],
                    tags=row['tags'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    version=row['version'],
                    parent_id=row['parent_id'],
                    shared_with=row['shared_with']
                )
                for row in rows
            ]
    
    async def update_knowledge(self,
                             knowledge_id: str,
                             content: Optional[Dict[str, Any]] = None,
                             confidence: Optional[float] = None,
                             tags: Optional[List[str]] = None) -> bool:
        """Update existing knowledge item"""
        
        updates = []
        params = []
        
        if content is not None:
            updates.append("content = $1")
            params.append(json.dumps(content))
            
        if confidence is not None:
            updates.append("confidence = $1")
            params.append(confidence)
            
        if tags is not None:
            updates.append("tags = $1")
            params.append(tags)
            
        if not updates:
            return False
            
        params.append(knowledge_id)
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(f"""
                UPDATE agent_knowledge
                SET {', '.join(updates)}, updated_at = NOW(), version = version + 1
                WHERE id = ${len(params)}
            """, *params)
            
            return result == "UPDATE 1"
    
    async def share_knowledge(self,
                            knowledge_id: str,
                            target_agents: List[str]) -> bool:
        """Share knowledge with other agents"""
        
        async with self.pool.acquire() as conn:
            # Get current shared_with list
            current = await conn.fetchval("""
                SELECT shared_with FROM agent_knowledge WHERE id = $1
            """, knowledge_id)
            
            if current is None:
                return False
                
            # Add new agents
            updated_shared = list(set(current + target_agents))
            
            result = await conn.execute("""
                UPDATE agent_knowledge
                SET shared_with = $1, updated_at = NOW()
                WHERE id = $2
            """, updated_shared, knowledge_id)
            
            return result == "UPDATE 1"
    
    async def add_relationship(self,
                              source_id: str,
                              target_id: str,
                              relationship_type: str,
                              strength: float = 1.0) -> bool:
        """Add relationship between knowledge items"""
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO knowledge_relationships
                    (source_knowledge_id, target_knowledge_id, relationship_type, strength)
                    VALUES ($1, $2, $3, $4)
                """, source_id, target_id, relationship_type, strength)
                return True
            except asyncpg.UniqueViolationError:
                return False
    
    async def get_related_knowledge(self,
                                  knowledge_id: str,
                                  relationship_type: Optional[str] = None) -> List[KnowledgeItem]:
        """Get knowledge items related to this one"""
        
        query = """
            SELECT ak.* FROM agent_knowledge ak
            JOIN knowledge_relationships kr ON ak.id = kr.target_knowledge_id
            WHERE kr.source_knowledge_id = $1
        """
        params = [knowledge_id]
        
        if relationship_type:
            query += " AND kr.relationship_type = $2"
            params.append(relationship_type)
            
        query += " ORDER BY kr.strength DESC"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            return [
                KnowledgeItem(
                    id=row['id'],
                    category=row['category'],
                    content=row['content'],
                    confidence=row['confidence'],
                    source_agent=row['source_agent'],
                    tags=row['tags'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    version=row['version'],
                    parent_id=row['parent_id'],
                    shared_with=row['shared_with']
                )
                for row in rows
            ]
    
    async def validate_knowledge(self,
                             knowledge_id: str,
                             validator_agent: str,
                             validation_type: str,
                             validation_data: Dict[str, Any],
                             confidence_change: float) -> bool:
        """Validate knowledge through cross-agent verification"""
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO knowledge_validation
                (knowledge_id, validator_agent, validation_type, validation_data, confidence_change)
                VALUES ($1, $2, $3, $4, $5)
            """, knowledge_id, validator_agent, validation_type, json.dumps(validation_data), confidence_change)
            
            # Update knowledge confidence
            await conn.execute("""
                UPDATE agent_knowledge
                SET confidence = confidence + $1,
                    updated_at = NOW()
                WHERE id = $2
            """, confidence_change, knowledge_id)
            
            return True
    
    async def get_knowledge_summary(self,
                                  source_agent: Optional[str] = None,
                                  category: Optional[str] = None) -> Dict[str, Any]:
        """Get summary statistics for knowledge"""
        
        query = """
            SELECT 
                COUNT(*) as total_items,
                COUNT(DISTINCT category) as categories,
                AVG(confidence) as avg_confidence,
                COUNT(DISTINCT source_agent) as source_agents,
                COUNT(*) FILTER (WHERE array_length(shared_with, 1) > 0) as shared_items
            FROM agent_knowledge
            WHERE 1=1
        """
        params = []
        
        if source_agent:
            query += " AND source_agent = $1"
            params.append(source_agent)
            
        if category:
            query += f" AND category = ${len(params) + 1}"
            params.append(category)
        
        async with self.pool.acquire() as conn:
            summary = await conn.fetchrow(query, *params)
            
            return dict(summary)
    
    async def search_knowledge(self,
                           query: str,
                           source_agents: Optional[List[str]] = None,
                           min_confidence: float = 0.0,
                           limit: int = 50) -> List[KnowledgeItem]:
        """Search knowledge using full-text search"""
        
        search_query = """
            SELECT * FROM agent_knowledge
            WHERE (content->>'text') ILIKE $1
              AND confidence >= $2
        """
        params = [f'%{query}%', min_confidence]
        
        if source_agents:
            placeholders = ','.join(f'${i+3}' for i in range(len(source_agents)))
            search_query += f" AND source_agent IN ({placeholders})"
            params.extend(source_agents)
        
        search_query += " ORDER BY confidence DESC LIMIT $3"
        params.append(limit)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(search_query, *params)
            
            return [
                KnowledgeItem(
                    id=row['id'],
                    category=row['category'],
                    content=row['content'],
                    confidence=row['confidence'],
                    source_agent=row['source_agent'],
                    tags=row['tags'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    version=row['version'],
                    parent_id=row['parent_id'],
                    shared_with=row['shared_with']
                )
                for row in rows
            ]
