"""
Base AI Agent class with integrated Three-Tier Memory System
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import asyncpg
from uuid import uuid4

from auren.core.memory import (
    UnifiedMemorySystem,
    UnifiedMemoryQuery,
    MemoryType,
    MemoryTier,
    UnifiedMemoryResult
)
from auren.config.production_settings import settings
from auren.core.logging_config import get_logger

logger = get_logger(__name__)


class BaseAIAgent(ABC):
    """
    Base class for all AUREN AI agents with integrated memory capabilities.
    
    This class provides:
    - Automatic connection to the universal three-tier memory system
    - Agent-specific memory isolation through namespacing
    - Memory control capabilities (priority, TTL, retention)
    - Standard memory operations (remember, recall, forget)
    - Event tracking and audit trails
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        agent_name: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new AI agent with memory system integration.
        
        Args:
            agent_id: Unique identifier for this agent instance
            agent_type: Type of agent (e.g., "medical", "research", "assistant")
            agent_name: Human-readable name for the agent
            description: Brief description of the agent's purpose
            metadata: Additional agent-specific metadata
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.description = description
        self.metadata = metadata or {}
        
        # Memory system will be initialized on first use
        self._memory_system: Optional[UnifiedMemorySystem] = None
        self._db_pool: Optional[asyncpg.Pool] = None
        
        # Agent state
        self.created_at = datetime.utcnow()
        self.is_active = True
        self.memory_stats = {
            "total_memories": 0,
            "hot_memories": 0,
            "recent_recalls": 0,
            "memory_efficiency": 1.0
        }
        
        logger.info(f"Initialized {self.agent_type} agent: {self.agent_name} (ID: {self.agent_id})")
    
    async def initialize(self):
        """Initialize the agent's connections and memory system."""
        await self._setup_database_pool()
        await self._setup_memory_system()
        await self._register_agent()
    
    async def _setup_database_pool(self):
        """Create database connection pool for the agent."""
        self._db_pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=2,
            max_size=10,
            timeout=30.0,
            command_timeout=10.0
        )
    
    async def _setup_memory_system(self):
        """Initialize connection to the universal memory system."""
        self._memory_system = UnifiedMemorySystem(
            redis_url=settings.redis_url,
            postgresql_pool=self._db_pool,
            chromadb_host=settings.chromadb_host,
            chromadb_port=settings.chromadb_port
        )
        await self._memory_system.initialize()
        
        logger.info(f"Agent {self.agent_id} connected to universal memory system")
    
    async def _register_agent(self):
        """Register this agent in the system."""
        async with self._db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO agents (agent_id, agent_type, agent_name, description, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (agent_id) DO UPDATE
                SET agent_name = EXCLUDED.agent_name,
                    description = EXCLUDED.description,
                    metadata = EXCLUDED.metadata,
                    last_active = NOW()
            """, self.agent_id, self.agent_type, self.agent_name, 
                self.description, self.metadata, self.created_at)
    
    @property
    def memory(self) -> UnifiedMemorySystem:
        """Get the memory system instance."""
        if not self._memory_system:
            raise RuntimeError("Agent not initialized. Call await agent.initialize() first.")
        return self._memory_system
    
    async def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.EXPERIENCE,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None
    ) -> str:
        """
        Store a new memory in the three-tier system.
        
        Args:
            content: The memory content to store
            memory_type: Type of memory (EXPERIENCE, KNOWLEDGE, SKILL, etc.)
            importance: Importance score (0.0-1.0) affecting tier placement
            tags: Optional tags for categorization
            metadata: Additional memory metadata
            ttl_seconds: Optional TTL for hot tier (agent-controlled retention)
        
        Returns:
            memory_id: Unique identifier for the stored memory
        """
        # Enrich metadata with agent context
        enriched_metadata = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            **(metadata or {})
        }
        
        # Agent-specific TTL based on importance if not specified
        if ttl_seconds is None and importance < 0.3:
            ttl_seconds = 3600  # Low importance: 1 hour in hot tier
        elif ttl_seconds is None and importance < 0.7:
            ttl_seconds = 86400  # Medium importance: 24 hours
        # High importance: No TTL (stays until memory pressure)
        
        memory_id = await self.memory.store_memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags,
            metadata=enriched_metadata,
            user_id=self.agent_id,  # Use agent_id as user_id for isolation
            agent_id=self.agent_id,
            ttl_seconds=ttl_seconds
        )
        
        self.memory_stats["total_memories"] += 1
        logger.debug(f"Agent {self.agent_id} stored memory {memory_id} with importance {importance}")
        
        return memory_id
    
    async def recall(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10,
        min_confidence: float = 0.0,
        time_range: Optional[tuple] = None,
        include_semantic: bool = True
    ) -> List[UnifiedMemoryResult]:
        """
        Retrieve memories matching the query.
        
        Args:
            query: Search query (semantic or keyword-based)
            memory_types: Filter by specific memory types
            limit: Maximum number of results
            min_confidence: Minimum confidence score for results
            time_range: Optional (start_date, end_date) tuple
            include_semantic: Whether to include semantic search
        
        Returns:
            List of matching memories from all tiers
        """
        search_query = UnifiedMemoryQuery(
            query=query,
            agent_id=self.agent_id,  # Automatically filter to this agent
            memory_types=memory_types,
            limit=limit,
            time_range=time_range,
            min_confidence=min_confidence,
            include_redis=True,
            include_postgres=True,
            include_chromadb=include_semantic
        )
        
        results = await self.memory.search_memories(search_query)
        
        self.memory_stats["recent_recalls"] += 1
        logger.debug(f"Agent {self.agent_id} recalled {len(results)} memories for query: {query}")
        
        return results
    
    async def recall_by_id(self, memory_id: str) -> Optional[UnifiedMemoryResult]:
        """Retrieve a specific memory by ID."""
        return await self.memory.retrieve_memory(
            memory_id=memory_id,
            agent_id=self.agent_id
        )
    
    async def update_memory_importance(
        self,
        memory_id: str,
        new_importance: float,
        reason: str = "Agent-initiated update"
    ):
        """
        Update the importance of a memory, potentially changing its tier.
        
        Args:
            memory_id: ID of the memory to update
            new_importance: New importance score (0.0-1.0)
            reason: Reason for the update (for audit trail)
        """
        # Update in Redis if it's a hot memory
        await self.memory.redis_tier.update_memory_priority(
            memory_id=memory_id,
            agent_id=self.agent_id,
            new_priority=new_importance
        )
        
        # Update in PostgreSQL
        await self.memory.update_memory(
            memory_id=memory_id,
            updates={"importance": new_importance},
            agent_id=self.agent_id
        )
        
        logger.info(f"Agent {self.agent_id} updated memory {memory_id} importance to {new_importance}: {reason}")
    
    async def forget(self, memory_id: str, reason: str = "Agent-initiated deletion"):
        """
        Remove a memory from all tiers.
        
        Args:
            memory_id: ID of the memory to delete
            reason: Reason for deletion (for audit trail)
        """
        await self.memory.delete_memory(
            memory_id=memory_id,
            agent_id=self.agent_id
        )
        
        self.memory_stats["total_memories"] = max(0, self.memory_stats["total_memories"] - 1)
        logger.info(f"Agent {self.agent_id} deleted memory {memory_id}: {reason}")
    
    async def consolidate_memories(
        self,
        time_window: int = 86400,
        similarity_threshold: float = 0.8
    ) -> List[str]:
        """
        Consolidate similar memories to optimize storage.
        
        Args:
            time_window: Time window in seconds to consider for consolidation
            similarity_threshold: Similarity score threshold for consolidation
        
        Returns:
            List of consolidated memory IDs
        """
        # This is a complex operation that would involve:
        # 1. Retrieving recent memories
        # 2. Computing similarity between memories
        # 3. Merging similar memories
        # 4. Updating importance scores
        
        # For now, return empty list - this would be implemented based on specific needs
        logger.info(f"Agent {self.agent_id} initiated memory consolidation")
        return []
    
    async def share_memory(
        self,
        memory_id: str,
        target_agents: List[str],
        share_type: str = "read_only"
    ):
        """
        Share a memory with other agents.
        
        Args:
            memory_id: ID of the memory to share
            target_agents: List of agent IDs to share with
            share_type: Type of sharing ("read_only", "collaborative")
        """
        # Retrieve the memory
        memory = await self.recall_by_id(memory_id)
        if not memory:
            logger.warning(f"Agent {self.agent_id} tried to share non-existent memory {memory_id}")
            return
        
        # Update metadata to include sharing information
        sharing_metadata = {
            "shared_by": self.agent_id,
            "shared_with": target_agents,
            "share_type": share_type,
            "shared_at": datetime.utcnow().isoformat()
        }
        
        await self.memory.update_memory(
            memory_id=memory_id,
            updates={"sharing": sharing_metadata},
            agent_id=self.agent_id
        )
        
        logger.info(f"Agent {self.agent_id} shared memory {memory_id} with {target_agents}")
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get detailed statistics about the agent's memory usage."""
        stats = await self.memory.get_system_stats()
        
        # Filter to this agent's stats
        agent_stats = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "total_memories": self.memory_stats["total_memories"],
            "recent_recalls": self.memory_stats["recent_recalls"],
            "memory_efficiency": self.memory_stats["memory_efficiency"],
            "tier_distribution": {
                "hot": stats.get("redis", {}).get(f"agent:{self.agent_id}", 0),
                "warm": stats.get("postgres", {}).get(f"agent:{self.agent_id}", 0),
                "cold": stats.get("chromadb", {}).get(f"agent:{self.agent_id}", 0)
            }
        }
        
        return agent_stats
    
    async def optimize_memory_usage(self):
        """
        Trigger agent-specific memory optimization.
        
        This method allows agents to define custom retention policies
        and optimization strategies based on their specific needs.
        """
        # Define agent-specific criteria for memory retention
        retention_criteria = {
            "min_importance": 0.3,
            "max_age_days": 30,
            "max_memories": settings.agent_memory_max_items,
            "preserve_tags": ["critical", "learning", "skill"]
        }
        
        # Let the memory system optimize based on criteria
        retained_memories = await self.memory.redis_tier.agent_decide_retention(
            agent_id=self.agent_id,
            criteria=retention_criteria
        )
        
        logger.info(f"Agent {self.agent_id} optimized memory usage, retained {len(retained_memories)} memories")
    
    async def cleanup(self):
        """Clean up agent resources."""
        if self._db_pool:
            await self._db_pool.close()
        
        logger.info(f"Agent {self.agent_id} cleaned up resources")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method that each agent must implement.
        
        Args:
            input_data: Input data for the agent to process
        
        Returns:
            Processing results
        """
        pass
    
    @abstractmethod
    async def learn(self, feedback: Dict[str, Any]) -> None:
        """
        Learning method for agents to improve based on feedback.
        
        Args:
            feedback: Feedback data for learning
        """
        pass 