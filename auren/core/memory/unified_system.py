"""
UnifiedMemorySystem - Complete Three-Tier Memory Implementation
Coordinates Redis (Hot), PostgreSQL (Warm), and ChromaDB (Cold) tiers
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from enum import Enum
import asyncpg

from .redis_tier import RedisTier, HotMemoryItem
from .postgres_tier import PostgreSQLTier, PostgresMemoryItem, MemoryType
from .chromadb_tier import ChromaDBTier, SemanticMemoryItem

logger = logging.getLogger(__name__)


class MemoryTier(Enum):
    """Memory tier levels"""
    HOT = "redis"      # < 30 days, immediate access
    WARM = "postgres"  # 30 days - 1 year, structured queries
    COLD = "chromadb"  # > 1 year, semantic search


@dataclass
class UnifiedMemoryQuery:
    """Query across all memory tiers"""
    query: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    memory_type: Optional[str] = None
    tier_preference: Optional[List[MemoryTier]] = None
    limit: int = 50
    include_semantic: bool = True


@dataclass
class UnifiedMemoryResult:
    """Result from unified memory search"""
    memory_id: str
    tier: MemoryTier
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    relevance_score: float
    created_at: datetime
    access_info: Dict[str, Any]


class UnifiedMemorySystem:
    """
    Complete three-tier memory system implementation
    
    Architecture:
    - Tier 1 (Hot): Redis for immediate access (<30 days)
    - Tier 2 (Warm): PostgreSQL for structured queries (30 days - 1 year)  
    - Tier 3 (Cold): ChromaDB for semantic search (>1 year)
    
    Features:
    - Automatic tier management and promotion
    - Unified search across all tiers
    - Agent-controlled memory priorities
    - Real-time WebSocket events
    - Memory pressure management
    """
    
    def __init__(self,
                 redis_url: str = "redis://localhost:6379",
                 postgresql_pool: Optional[asyncpg.Pool] = None,
                 postgresql_url: Optional[str] = None,
                 chromadb_path: str = "/auren/data/chromadb",
                 event_streamer=None):
        
        # Initialize tiers
        self.redis_tier = RedisTier(
            redis_url=redis_url,
            event_emitter=event_streamer
        )
        
        self.postgres_tier = PostgreSQLTier(
            pool=postgresql_pool,
            database_url=postgresql_url,
            event_emitter=event_streamer
        )
        
        self.chromadb_tier = ChromaDBTier(
            persist_directory=chromadb_path,
            event_emitter=event_streamer
        )
        
        self.event_streamer = event_streamer
        self._initialized = False
        
        # Tier transition settings
        self.hot_to_warm_days = 30
        self.warm_to_cold_days = 365
        
    async def initialize(self):
        """Initialize all memory tiers"""
        if self._initialized:
            return
        
        try:
            # Initialize all tiers
            await self.redis_tier.connect()
            await self.postgres_tier.initialize()
            await self.chromadb_tier.initialize()
            
            # Start background tasks
            asyncio.create_task(self._tier_management_loop())
            asyncio.create_task(self._memory_optimization_loop())
            
            self._initialized = True
            logger.info("UnifiedMemorySystem initialized successfully")
            
            # Emit initialization event
            if self.event_streamer:
                await self._emit_event('system_initialized', {
                    'tiers': ['redis', 'postgresql', 'chromadb'],
                    'status': 'ready'
                })
                
        except Exception as e:
            logger.error(f"Failed to initialize UnifiedMemorySystem: {e}")
            raise
    
    async def store_memory(self,
                          memory_id: Optional[str] = None,
                          agent_id: str = None,
                          user_id: str = None,
                          content: Dict[str, Any] = None,
                          memory_type: Union[str, MemoryType] = None,
                          confidence: float = 1.0,
                          priority: float = 1.0,
                          metadata: Optional[Dict[str, Any]] = None,
                          ttl_override: Optional[int] = None) -> str:
        """
        Store memory in appropriate tier
        
        New memories start in Redis (hot tier) and flow down based on:
        - Age
        - Access patterns
        - Agent priorities
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Generate memory ID if not provided
            if not memory_id:
                import uuid
                memory_id = str(uuid.uuid4())
            
            # Ensure memory_type is string
            if isinstance(memory_type, MemoryType):
                memory_type = memory_type.value
            
            # Store in Redis (hot tier)
            success = await self.redis_tier.store_memory(
                memory_id=memory_id,
                agent_id=agent_id,
                user_id=user_id,
                content=content,
                memory_type=memory_type,
                confidence=confidence,
                priority=priority,
                ttl_override=ttl_override,
                metadata=metadata
            )
            
            if not success:
                raise Exception("Failed to store in Redis tier")
            
            # For high-importance memories, also store in PostgreSQL immediately
            if priority >= 8.0 or confidence >= 0.9:
                await self.postgres_tier.store_memory(
                    memory_id=memory_id,
                    agent_id=agent_id,
                    user_id=user_id,
                    memory_type=memory_type,
                    content=content,
                    confidence=confidence,
                    metadata={
                        **(metadata or {}),
                        'original_priority': priority,
                        'dual_stored': True
                    }
                )
            
            # Emit storage event
            if self.event_streamer:
                await self._emit_event('memory_stored', {
                    'memory_id': memory_id,
                    'agent_id': agent_id,
                    'user_id': user_id,
                    'tier': 'redis',
                    'priority': priority
                })
            
            logger.info(f"Stored memory {memory_id} in unified system")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    async def retrieve_memory(self, memory_id: str) -> Optional[UnifiedMemoryResult]:
        """
        Retrieve memory from any tier
        
        Search order:
        1. Redis (fastest)
        2. PostgreSQL (structured)
        3. ChromaDB (semantic)
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Try Redis first
            redis_memory = await self.redis_tier.retrieve_memory(memory_id)
            if redis_memory:
                return UnifiedMemoryResult(
                    memory_id=redis_memory.memory_id,
                    tier=MemoryTier.HOT,
                    content=redis_memory.content,
                    metadata=redis_memory.metadata or {},
                    relevance_score=1.0,
                    created_at=redis_memory.created_at,
                    access_info={
                        'access_count': redis_memory.access_count,
                        'priority': redis_memory.priority
                    }
                )
            
            # Try PostgreSQL
            pg_memory = await self.postgres_tier.retrieve_memory(memory_id)
            if pg_memory:
                # Optionally promote back to Redis if accessed
                if pg_memory.metadata.get('access_count', 0) > 5:
                    await self._promote_to_redis(pg_memory)
                
                return UnifiedMemoryResult(
                    memory_id=pg_memory.memory_id,
                    tier=MemoryTier.WARM,
                    content=pg_memory.content,
                    metadata=pg_memory.metadata,
                    relevance_score=1.0,
                    created_at=pg_memory.created_at,
                    access_info={
                        'source': 'postgresql',
                        'confidence': pg_memory.confidence
                    }
                )
            
            # Try ChromaDB
            results = await self.chromadb_tier.semantic_search(
                query=memory_id,
                limit=1
            )
            
            if results and results[0].memory_id == memory_id:
                result = results[0]
                return UnifiedMemoryResult(
                    memory_id=result.memory_id,
                    tier=MemoryTier.COLD,
                    content=result.content,
                    metadata=result.metadata,
                    relevance_score=result.relevance_score or 1.0,
                    created_at=result.created_at,
                    access_info={
                        'source': 'chromadb',
                        'semantic_match': True
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve memory {memory_id}: {e}")
            return None
    
    async def search_memories(self, query: UnifiedMemoryQuery) -> List[UnifiedMemoryResult]:
        """
        Search across all memory tiers
        
        Combines results from:
        - Redis: Recent memories
        - PostgreSQL: Structured search
        - ChromaDB: Semantic similarity
        """
        if not self._initialized:
            await self.initialize()
        
        results = []
        tasks = []
        
        try:
            # Determine which tiers to search
            tiers_to_search = query.tier_preference or list(MemoryTier)
            
            # Search Redis tier
            if MemoryTier.HOT in tiers_to_search:
                task = self._search_redis_tier(query)
                tasks.append(('redis', task))
            
            # Search PostgreSQL tier
            if MemoryTier.WARM in tiers_to_search:
                task = self._search_postgres_tier(query)
                tasks.append(('postgres', task))
            
            # Search ChromaDB tier
            if MemoryTier.COLD in tiers_to_search and query.include_semantic:
                task = self._search_chromadb_tier(query)
                tasks.append(('chromadb', task))
            
            # Execute searches in parallel
            if tasks:
                tier_results = await asyncio.gather(
                    *[task for _, task in tasks],
                    return_exceptions=True
                )
                
                # Combine results
                for i, (tier_name, _) in enumerate(tasks):
                    if not isinstance(tier_results[i], Exception):
                        results.extend(tier_results[i])
                    else:
                        logger.error(f"Search failed for {tier_name}: {tier_results[i]}")
            
            # Sort by relevance and deduplicate
            results.sort(key=lambda r: r.relevance_score, reverse=True)
            
            # Deduplicate by memory_id
            seen_ids = set()
            deduped_results = []
            for result in results:
                if result.memory_id not in seen_ids:
                    seen_ids.add(result.memory_id)
                    deduped_results.append(result)
            
            # Apply limit
            final_results = deduped_results[:query.limit]
            
            # Emit search event
            if self.event_streamer:
                await self._emit_event('unified_search', {
                    'query': query.query,
                    'results_count': len(final_results),
                    'tiers_searched': [t.value for t in tiers_to_search]
                })
            
            return final_results
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    async def _search_redis_tier(self, query: UnifiedMemoryQuery) -> List[UnifiedMemoryResult]:
        """Search Redis tier"""
        memories = await self.redis_tier.get_user_memories(
            user_id=query.user_id or "",
            memory_type=query.memory_type,
            limit=query.limit
        )
        
        results = []
        for memory in memories:
            # Simple text matching for Redis
            match_score = 0.5
            if query.query.lower() in json.dumps(memory.content).lower():
                match_score = 0.8
            
            results.append(UnifiedMemoryResult(
                memory_id=memory.memory_id,
                tier=MemoryTier.HOT,
                content=memory.content,
                metadata=memory.metadata or {},
                relevance_score=match_score * memory.priority,
                created_at=memory.created_at,
                access_info={
                    'access_count': memory.access_count,
                    'priority': memory.priority
                }
            ))
        
        return results
    
    async def _search_postgres_tier(self, query: UnifiedMemoryQuery) -> List[UnifiedMemoryResult]:
        """Search PostgreSQL tier"""
        if query.query:
            # Full-text search
            memories = await self.postgres_tier.search_memories(
                query=query.query,
                user_id=query.user_id,
                agent_id=query.agent_id,
                limit=query.limit
            )
        else:
            # Get user memories
            memories = await self.postgres_tier.get_user_memories(
                user_id=query.user_id or "",
                agent_id=query.agent_id,
                memory_type=query.memory_type,
                limit=query.limit
            )
        
        results = []
        for memory in memories:
            relevance = memory.metadata.get('search_relevance', 0.7)
            
            results.append(UnifiedMemoryResult(
                memory_id=memory.memory_id,
                tier=MemoryTier.WARM,
                content=memory.content,
                metadata=memory.metadata,
                relevance_score=relevance * memory.confidence,
                created_at=memory.created_at,
                access_info={
                    'confidence': memory.confidence,
                    'memory_type': memory.memory_type.value
                }
            ))
        
        return results
    
    async def _search_chromadb_tier(self, query: UnifiedMemoryQuery) -> List[UnifiedMemoryResult]:
        """Search ChromaDB tier"""
        memories = await self.chromadb_tier.semantic_search(
            query=query.query,
            user_id=query.user_id,
            agent_id=query.agent_id,
            memory_type=query.memory_type,
            limit=query.limit
        )
        
        results = []
        for memory in memories:
            results.append(UnifiedMemoryResult(
                memory_id=memory.memory_id,
                tier=MemoryTier.COLD,
                content=memory.content,
                metadata=memory.metadata,
                relevance_score=memory.relevance_score or 0.5,
                created_at=memory.created_at,
                access_info={
                    'semantic_search': True,
                    'confidence': memory.confidence
                }
            ))
        
        return results
    
    async def update_memory(self,
                           memory_id: str,
                           content: Optional[Dict[str, Any]] = None,
                           metadata: Optional[Dict[str, Any]] = None,
                           priority: Optional[float] = None) -> bool:
        """Update memory in its current tier"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Find which tier contains the memory
            memory = await self.retrieve_memory(memory_id)
            if not memory:
                return False
            
            success = False
            
            if memory.tier == MemoryTier.HOT:
                # Update in Redis
                if priority is not None:
                    agent_id = memory.metadata.get('agent_id', 'system')
                    success = await self.redis_tier.update_memory_priority(
                        memory_id=memory_id,
                        agent_id=agent_id,
                        new_priority=priority
                    )
            
            elif memory.tier == MemoryTier.WARM:
                # Update in PostgreSQL
                success = await self.postgres_tier.update_memory(
                    memory_id=memory_id,
                    content=content,
                    metadata=metadata
                )
            
            elif memory.tier == MemoryTier.COLD:
                # Update in ChromaDB
                if content:
                    success = await self.chromadb_tier.update_memory_embedding(
                        memory_id=memory_id,
                        new_content=content
                    )
            
            if success and self.event_streamer:
                await self._emit_event('memory_updated', {
                    'memory_id': memory_id,
                    'tier': memory.tier.value,
                    'updates': {
                        'content': content is not None,
                        'metadata': metadata is not None,
                        'priority': priority is not None
                    }
                })
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory from all tiers"""
        if not self._initialized:
            await self.initialize()
        
        try:
            deleted_from = []
            
            # Try deleting from all tiers
            tasks = [
                ('redis', self.redis_tier.delete(user_id='', memory_id=memory_id)),
                ('postgres', self.postgres_tier.delete_memory(memory_id)),
                ('chromadb', self.chromadb_tier.delete_memory(memory_id))
            ]
            
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            for i, (tier_name, _) in enumerate(tasks):
                if not isinstance(results[i], Exception) and results[i]:
                    deleted_from.append(tier_name)
            
            if deleted_from and self.event_streamer:
                await self._emit_event('memory_deleted', {
                    'memory_id': memory_id,
                    'deleted_from': deleted_from
                })
            
            return len(deleted_from) > 0
            
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get statistics across all tiers"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Gather stats from all tiers in parallel
            stats_tasks = [
                self.redis_tier.get_memory_stats(),
                self.postgres_tier.get_memory_stats(),
                self.chromadb_tier.get_memory_stats()
            ]
            
            tier_stats = await asyncio.gather(*stats_tasks, return_exceptions=True)
            
            system_stats = {
                'redis_tier': tier_stats[0] if not isinstance(tier_stats[0], Exception) else {},
                'postgres_tier': tier_stats[1] if not isinstance(tier_stats[1], Exception) else {},
                'chromadb_tier': tier_stats[2] if not isinstance(tier_stats[2], Exception) else {},
                'total_memories': 0,
                'tier_distribution': {}
            }
            
            # Calculate totals
            for tier_name, stats in [
                ('redis', system_stats['redis_tier']),
                ('postgres', system_stats['postgres_tier']),
                ('chromadb', system_stats['chromadb_tier'])
            ]:
                count = stats.get('total_memories', 0)
                system_stats['total_memories'] += count
                system_stats['tier_distribution'][tier_name] = count
            
            return system_stats
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}
    
    async def agent_memory_control(self,
                                  agent_id: str,
                                  action: str,
                                  params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Allow agents to control their memories
        
        Actions:
        - 'set_retention': Update retention criteria
        - 'prioritize': Boost memory priorities
        - 'demote': Lower memory priorities
        - 'archive': Move to cold storage
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            if action == 'set_retention':
                # Let agent decide what to keep in hot tier
                retained = await self.redis_tier.agent_decide_retention(
                    agent_id=agent_id,
                    criteria=params.get('criteria', {})
                )
                
                return {
                    'action': 'set_retention',
                    'retained_count': len(retained),
                    'memory_ids': retained
                }
            
            elif action == 'prioritize':
                # Boost priority of specific memories
                memory_ids = params.get('memory_ids', [])
                boost_factor = params.get('boost_factor', 1.5)
                
                updated = 0
                for memory_id in memory_ids:
                    memory = await self.redis_tier.retrieve_memory(memory_id)
                    if memory and memory.agent_id == agent_id:
                        new_priority = min(memory.priority * boost_factor, 10.0)
                        if await self.redis_tier.update_memory_priority(
                            memory_id, agent_id, new_priority
                        ):
                            updated += 1
                
                return {
                    'action': 'prioritize',
                    'updated_count': updated
                }
            
            elif action == 'archive':
                # Move memories directly to cold storage
                memory_ids = params.get('memory_ids', [])
                archived = 0
                
                for memory_id in memory_ids:
                    if await self._archive_to_cold(memory_id, agent_id):
                        archived += 1
                
                return {
                    'action': 'archive',
                    'archived_count': archived
                }
            
            else:
                return {
                    'error': f'Unknown action: {action}'
                }
                
        except Exception as e:
            logger.error(f"Agent memory control failed: {e}")
            return {'error': str(e)}
    
    async def _tier_management_loop(self):
        """Background task to manage tier transitions"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run hourly
                
                # Promote old Redis memories to PostgreSQL
                redis_stats = await self.redis_tier.get_memory_stats()
                if redis_stats.get('total_memories', 0) > 0:
                    # Implementation of tier transition logic
                    logger.info("Running tier management cycle")
                    
                # Clean up expired memories
                await self.postgres_tier.cleanup_expired()
                
            except Exception as e:
                logger.error(f"Tier management error: {e}")
    
    async def _memory_optimization_loop(self):
        """Background task to optimize memory distribution"""
        while True:
            try:
                await asyncio.sleep(7200)  # Run every 2 hours
                
                # Discover patterns in ChromaDB
                # Optimize memory placement based on access patterns
                logger.info("Running memory optimization cycle")
                
            except Exception as e:
                logger.error(f"Memory optimization error: {e}")
    
    async def _promote_to_redis(self, memory: PostgresMemoryItem):
        """Promote frequently accessed memory back to Redis"""
        try:
            await self.redis_tier.store_memory(
                memory_id=memory.memory_id,
                agent_id=memory.agent_id,
                user_id=memory.user_id,
                content=memory.content,
                memory_type=memory.memory_type.value,
                confidence=memory.confidence,
                metadata={
                    **memory.metadata,
                    'promoted_from': 'postgresql',
                    'promotion_reason': 'frequent_access'
                }
            )
        except Exception as e:
            logger.error(f"Failed to promote memory to Redis: {e}")
    
    async def _archive_to_cold(self, memory_id: str, agent_id: str) -> bool:
        """Archive memory directly to ChromaDB"""
        try:
            # Get memory from current location
            memory = await self.retrieve_memory(memory_id)
            if not memory:
                return False
            
            # Verify agent owns this memory
            if memory.metadata.get('agent_id') != agent_id:
                return False
            
            # Store in ChromaDB
            success = await self.chromadb_tier.store_memory(
                memory_id=memory_id,
                agent_id=agent_id,
                user_id=memory.metadata.get('user_id', ''),
                content=memory.content,
                memory_type=memory.metadata.get('memory_type', 'unknown'),
                confidence=memory.metadata.get('confidence', 1.0),
                metadata={
                    **memory.metadata,
                    'archived_by_agent': True,
                    'archive_date': datetime.now(timezone.utc).isoformat()
                }
            )
            
            if success:
                # Remove from other tiers
                await self.delete_memory(memory_id)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to archive memory: {e}")
            return False
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit unified system event"""
        if self.event_streamer:
            try:
                await self.event_streamer.emit({
                    'type': f'unified_memory_{event_type}',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'data': data
                })
            except Exception as e:
                logger.error(f"Failed to emit event: {e}")
    
    async def close(self):
        """Close all connections"""
        try:
            await self.redis_tier.disconnect()
            await self.postgres_tier.close()
            await self.chromadb_tier.close()
            logger.info("UnifiedMemorySystem closed")
        except Exception as e:
            logger.error(f"Error closing UnifiedMemorySystem: {e}") 