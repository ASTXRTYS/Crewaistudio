"""
Redis Tier - Working Memory Implementation
Provides sub-10ms access for recent memories (last 30 days)
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisMemoryTier:
    """
    Redis-based working memory tier.
    
    Features:
    - Sub-10ms access latency
    - Automatic TTL management (30 days)
    - Memory indexing by user and agent
    - Query caching for repeated access
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.ttl_days = 30
        self.cache_ttl_hours = 1
        
    async def connect(self) -> bool:
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Redis tier connected")
            return True
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            return False
            
    async def store(self,
                   memory_id: str,
                   user_id: str,
                   agent_id: str,
                   content: Dict[str, Any],
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store memory in Redis with automatic indexing.
        
        Args:
            memory_id: Unique memory identifier
            user_id: User who owns this memory
            agent_id: Agent that created this memory
            content: Memory content
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        
        if not self.redis_client:
            return False
            
        try:
            # Prepare memory data
            memory_data = {
                "id": memory_id,
                "user_id": user_id,
                "agent_id": agent_id,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat(),
                "access_count": 0,
                "tier": "redis"
            }
            
            # Store memory with TTL
            key = f"mem:{user_id}:{memory_id}"
            ttl_seconds = self.ttl_days * 24 * 60 * 60
            
            await self.redis_client.setex(
                key,
                ttl_seconds,
                json.dumps(memory_data)
            )
            
            # Index by user
            user_index = f"idx:user:{user_id}"
            score = datetime.utcnow().timestamp()
            await self.redis_client.zadd(user_index, {memory_id: score})
            await self.redis_client.expire(user_index, ttl_seconds)
            
            # Index by agent
            agent_index = f"idx:agent:{agent_id}"
            await self.redis_client.zadd(agent_index, {memory_id: score})
            await self.redis_client.expire(agent_index, ttl_seconds)
            
            # Index by user-agent combination
            combined_index = f"idx:user_agent:{user_id}:{agent_id}"
            await self.redis_client.zadd(combined_index, {memory_id: score})
            await self.redis_client.expire(combined_index, ttl_seconds)
            
            logger.debug(f"Stored memory {memory_id} in Redis")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store in Redis: {e}")
            return False
            
    async def retrieve(self,
                      user_id: str,
                      query: Optional[str] = None,
                      agent_id: Optional[str] = None,
                      limit: int = 10,
                      offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve memories from Redis.
        
        Args:
            user_id: User ID to filter by
            query: Optional search query
            agent_id: Optional agent ID filter
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of memories
        """
        
        if not self.redis_client:
            return []
            
        try:
            # Check cache first if query provided
            if query:
                cache_key = f"cache:{user_id}:{agent_id or 'all'}:{hash(query)}"
                cached = await self.redis_client.get(cache_key)
                if cached:
                    logger.debug("Cache hit for query")
                    return json.loads(cached)[:limit]
            
            # Determine which index to use
            if agent_id:
                index_key = f"idx:user_agent:{user_id}:{agent_id}"
            else:
                index_key = f"idx:user:{user_id}"
                
            # Get memory IDs from index (sorted by timestamp)
            memory_ids = await self.redis_client.zrevrange(
                index_key,
                offset,
                offset + limit * 3  # Get extra for filtering
            )
            
            # Retrieve memories
            results = []
            for memory_id in memory_ids:
                key = f"mem:{user_id}:{memory_id}"
                data = await self.redis_client.get(key)
                
                if data:
                    memory = json.loads(data)
                    
                    # Increment access count
                    memory["access_count"] += 1
                    memory["last_accessed"] = datetime.utcnow().isoformat()
                    
                    # Update in Redis
                    await self.redis_client.set(key, json.dumps(memory))
                    
                    # Apply query filter if provided
                    if query:
                        content_str = json.dumps(memory["content"]).lower()
                        if query.lower() in content_str:
                            results.append(memory)
                    else:
                        results.append(memory)
                        
                    if len(results) >= limit:
                        break
                        
            # Cache results if query provided
            if query and results:
                cache_ttl = self.cache_ttl_hours * 60 * 60
                await self.redis_client.setex(
                    cache_key,
                    cache_ttl,
                    json.dumps(results)
                )
                
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve from Redis: {e}")
            return []
            
    async def delete(self, user_id: str, memory_id: str) -> bool:
        """Delete a memory from Redis"""
        if not self.redis_client:
            return False
            
        try:
            key = f"mem:{user_id}:{memory_id}"
            
            # Get memory to find agent_id
            data = await self.redis_client.get(key)
            if data:
                memory = json.loads(data)
                agent_id = memory.get("agent_id")
                
                # Remove from indexes
                await self.redis_client.zrem(f"idx:user:{user_id}", memory_id)
                if agent_id:
                    await self.redis_client.zrem(f"idx:agent:{agent_id}", memory_id)
                    await self.redis_client.zrem(
                        f"idx:user_agent:{user_id}:{agent_id}",
                        memory_id
                    )
                
                # Delete memory
                await self.redis_client.delete(key)
                logger.debug(f"Deleted memory {memory_id}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete from Redis: {e}")
            return False
            
    async def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get tier statistics"""
        if not self.redis_client:
            return {}
            
        try:
            stats = {
                "tier": "redis",
                "connected": True,
                "total_memories": 0,
                "users": set(),
                "agents": set()
            }
            
            # Scan for all memory keys
            cursor = 0
            pattern = f"mem:{user_id}:*" if user_id else "mem:*"
            
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match=pattern,
                    count=100
                )
                
                stats["total_memories"] += len(keys)
                
                # Extract user and agent info
                for key in keys:
                    parts = key.split(":")
                    if len(parts) >= 3:
                        stats["users"].add(parts[1])
                        
                        # Get agent from memory data
                        data = await self.redis_client.get(key)
                        if data:
                            memory = json.loads(data)
                            if "agent_id" in memory:
                                stats["agents"].add(memory["agent_id"])
                
                if cursor == 0:
                    break
                    
            # Convert sets to counts
            stats["unique_users"] = len(stats["users"])
            stats["unique_agents"] = len(stats["agents"])
            del stats["users"]
            del stats["agents"]
            
            # Get memory info
            info = await self.redis_client.info("memory")
            stats["memory_usage_mb"] = info.get("used_memory", 0) / (1024 * 1024)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {"tier": "redis", "connected": False, "error": str(e)}
            
    async def cleanup_expired(self) -> int:
        """
        Clean up expired memories.
        Redis handles this automatically with TTL, but this can force cleanup.
        
        Returns:
            Number of memories cleaned
        """
        # Redis handles expiration automatically
        # This method is here for API consistency
        return 0
        
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis tier connection closed") 