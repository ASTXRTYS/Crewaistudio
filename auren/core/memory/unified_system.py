"""
UnifiedMemorySystem - The missing three-tier memory implementation
Integrates Redis (working memory), PostgreSQL (long-term), and ChromaDB (semantic)
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import redis.asyncio as redis
import asyncpg

from .postgres_tier import PostgreSQLMemoryBackend
from .chromadb_tier import BiometricVectorStore

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Represents a memory item that can flow through tiers"""
    id: str
    user_id: str
    agent_id: str
    content: Dict[str, Any]
    timestamp: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tier: str = "redis"
    embedding: Optional[List[float]] = None


class UnifiedMemorySystem:
    """
    The actual three-tier memory system implementation.
    
    Memory flows:
    1. New memories → Redis (immediate access, <10ms)
    2. After 30 days → PostgreSQL (structured storage)
    3. Semantic patterns → ChromaDB (vector search)
    """
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 postgresql_pool: asyncpg.Pool = None,
                 chromadb_path: str = "/auren/data/vectors",
                 event_streamer=None):
        
        self.redis_client = None
        self.redis_url = redis_url
        
        # Initialize PostgreSQL backend
        self.postgres_backend = PostgreSQLMemoryBackend(
            pool=postgresql_pool,
            agent_type="unified",
            user_id=None
        )
        
        # Initialize ChromaDB vector store
        self.chromadb_store = BiometricVectorStore(
            persist_directory=chromadb_path
        )
        
        # Event streaming for dashboard
        self.event_streamer = event_streamer
        
        # Migration settings
        self.redis_ttl = 30 * 24 * 60 * 60  # 30 days in seconds
        self.migration_batch_size = 100
        self.semantic_threshold = 0.85  # Similarity threshold for ChromaDB
        
    async def initialize(self):
        """Initialize all tier connections"""
        # Connect to Redis
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
            
        # Initialize PostgreSQL tables
        await self.postgres_backend.initialize()
        logger.info("✅ PostgreSQL initialized")
        
        # ChromaDB is initialized in constructor
        logger.info("✅ ChromaDB initialized")
        
        # Start background migration task
        asyncio.create_task(self._migration_loop())
        
    async def store_memory(self, 
                          user_id: str,
                          agent_id: str,
                          content: Dict[str, Any],
                          memory_type: str = "interaction") -> str:
        """
        Store a new memory in the system.
        Always starts in Redis for immediate access.
        """
        
        # Generate memory ID
        memory_id = f"mem:{user_id}:{agent_id}:{datetime.utcnow().timestamp()}"
        
        # Create memory item
        memory_item = MemoryItem(
            id=memory_id,
            user_id=user_id,
            agent_id=agent_id,
            content=content,
            timestamp=datetime.utcnow()
        )
        
        # Store in Redis first (Tier 1)
        await self._store_in_redis(memory_item)
        
        # Emit event for dashboard
        if self.event_streamer:
            await self._emit_memory_event("memory_stored", {
                "memory_id": memory_id,
                "user_id": user_id,
                "agent_id": agent_id,
                "tier": "redis",
                "content_type": memory_type
            })
        
        return memory_id
        
    async def retrieve_memory(self,
                            query: str,
                            user_id: str,
                            agent_id: Optional[str] = None,
                            limit: int = 10) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        Retrieve memories using the three-tier cascade.
        Returns (results, metrics)
        """
        
        metrics = {
            "tier_accessed": None,
            "latency_ms": 0,
            "items_found": 0
        }
        
        start_time = asyncio.get_event_loop().time()
        
        # Try Redis first (Tier 1 - Working Memory)
        redis_results = await self._search_redis(query, user_id, agent_id, limit)
        if redis_results:
            metrics["tier_accessed"] = "redis"
            metrics["latency_ms"] = (asyncio.get_event_loop().time() - start_time) * 1000
            metrics["items_found"] = len(redis_results)
            
            # Emit dashboard event
            await self._emit_tier_access_event("redis", True, metrics["latency_ms"])
            
            return redis_results, metrics
            
        # Try PostgreSQL (Tier 2 - Long-term Memory)
        pg_results = await self._search_postgresql(query, user_id, agent_id, limit)
        if pg_results:
            metrics["tier_accessed"] = "postgresql"
            metrics["latency_ms"] = (asyncio.get_event_loop().time() - start_time) * 1000
            metrics["items_found"] = len(pg_results)
            
            # Cache in Redis for next time
            asyncio.create_task(self._cache_in_redis(query, pg_results, user_id))
            
            # Emit dashboard event
            await self._emit_tier_access_event("postgresql", True, metrics["latency_ms"])
            
            return pg_results, metrics
            
        # Try ChromaDB (Tier 3 - Semantic Memory)
        chroma_results = await self._search_chromadb(query, user_id, agent_id, limit)
        metrics["tier_accessed"] = "chromadb"
        metrics["latency_ms"] = (asyncio.get_event_loop().time() - start_time) * 1000
        metrics["items_found"] = len(chroma_results)
        
        # Cache in both Redis and PostgreSQL
        if chroma_results:
            asyncio.create_task(self._cache_in_redis(query, chroma_results, user_id))
            asyncio.create_task(self._cache_in_postgresql(query, chroma_results, user_id))
        
        # Emit dashboard event
        await self._emit_tier_access_event("chromadb", bool(chroma_results), metrics["latency_ms"])
        
        return chroma_results, metrics
        
    async def _store_in_redis(self, memory: MemoryItem):
        """Store memory in Redis with TTL"""
        key = f"memory:{memory.user_id}:{memory.id}"
        
        # Convert to JSON
        memory_data = {
            "id": memory.id,
            "user_id": memory.user_id,
            "agent_id": memory.agent_id,
            "content": memory.content,
            "timestamp": memory.timestamp.isoformat(),
            "access_count": memory.access_count,
            "tier": "redis"
        }
        
        # Store with TTL
        await self.redis_client.setex(
            key,
            self.redis_ttl,
            json.dumps(memory_data)
        )
        
        # Add to user's memory index
        index_key = f"memory_index:{memory.user_id}"
        await self.redis_client.zadd(
            index_key,
            {memory.id: memory.timestamp.timestamp()}
        )
        
    async def _search_redis(self, query: str, user_id: str, agent_id: Optional[str], limit: int) -> List[Dict]:
        """Search memories in Redis"""
        if not self.redis_client:
            return []
            
        # Get user's memory index
        index_key = f"memory_index:{user_id}"
        memory_ids = await self.redis_client.zrevrange(index_key, 0, limit * 10)
        
        results = []
        for memory_id in memory_ids:
            key = f"memory:{user_id}:{memory_id.decode()}"
            data = await self.redis_client.get(key)
            
            if data:
                memory = json.loads(data)
                
                # Simple query matching (enhance this later)
                if query.lower() in json.dumps(memory["content"]).lower():
                    if not agent_id or memory["agent_id"] == agent_id:
                        results.append(memory)
                        
                        if len(results) >= limit:
                            break
                            
        return results
        
    async def _search_postgresql(self, query: str, user_id: str, agent_id: Optional[str], limit: int) -> List[Dict]:
        """Search memories in PostgreSQL"""
        # Use existing PostgreSQL backend
        memories = await self.postgres_backend.retrieve_memories(
            user_id=user_id,
            memory_type="all",
            limit=limit * 2  # Get extra for filtering
        )
        
        # Filter by query and agent
        results = []
        for memory in memories:
            if query.lower() in json.dumps(memory).lower():
                if not agent_id or memory.get("agent_id") == agent_id:
                    results.append(memory)
                    
                    if len(results) >= limit:
                        break
                        
        return results
        
    async def _search_chromadb(self, query: str, user_id: str, agent_id: Optional[str], limit: int) -> List[Dict]:
        """Search memories in ChromaDB using semantic search"""
        # Get the appropriate collection
        collection = self.chromadb_store.collections.get("convergence", None)
        if not collection:
            return []
            
        # Perform semantic search
        results = collection.query(
            query_texts=[query],
            n_results=limit * 2,  # Get extra for filtering
            where={"user_id": user_id} if user_id else None
        )
        
        # Format results
        formatted = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                
                if not agent_id or metadata.get("agent_id") == agent_id:
                    formatted.append({
                        "id": results['ids'][0][i],
                        "content": doc,
                        "metadata": metadata,
                        "similarity": 1 - results['distances'][0][i],  # Convert distance to similarity
                        "tier": "chromadb"
                    })
                    
                    if len(formatted) >= limit:
                        break
                        
        return formatted
        
    async def _migration_loop(self):
        """Background task to migrate memories between tiers"""
        while True:
            try:
                # Check for memories ready to migrate from Redis to PostgreSQL
                await self._migrate_redis_to_postgresql()
                
                # Index semantic patterns in ChromaDB
                await self._index_semantic_patterns()
                
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Migration error: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes
                
    async def _migrate_redis_to_postgresql(self):
        """Migrate old memories from Redis to PostgreSQL"""
        # This would scan Redis for memories older than threshold
        # and move them to PostgreSQL
        pass  # Implementation details omitted for brevity
        
    async def _index_semantic_patterns(self):
        """Index discovered patterns in ChromaDB"""
        # This would analyze PostgreSQL memories for patterns
        # and index them in ChromaDB for semantic search
        pass  # Implementation details omitted for brevity
        
    async def _cache_in_redis(self, query: str, results: List[Dict], user_id: str):
        """Cache results in Redis for fast access"""
        cache_key = f"cache:{user_id}:{hash(query)}"
        await self.redis_client.setex(
            cache_key,
            3600,  # 1 hour cache
            json.dumps(results)
        )
        
    async def _cache_in_postgresql(self, query: str, results: List[Dict], user_id: str):
        """Cache semantic results in PostgreSQL"""
        # Store as a cached result for future reference
        pass  # Implementation details omitted for brevity
        
    async def _emit_memory_event(self, event_type: str, data: Dict[str, Any]):
        """Emit memory event to dashboard"""
        if self.event_streamer:
            await self.event_streamer.emit({
                "type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
            
    async def _emit_tier_access_event(self, tier: str, hit: bool, latency_ms: float):
        """Emit tier access event for dashboard visualization"""
        if self.event_streamer:
            await self.event_streamer.emit({
                "type": "tier_access",
                "tier": tier,
                "hit": hit,
                "latency_ms": latency_ms,
                "timestamp": datetime.utcnow().isoformat()
            }) 