"""
Resilient token tracking with Redis failover and eventual consistency.

Provides fault-tolerant token tracking that gracefully degrades
when Redis is unavailable and recovers automatically.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
import time

# Import Redis with fallback
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available - using local memory fallback")

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Record of token usage for tracking."""
    user_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    timestamp: datetime
    metadata: Dict[str, Any]


class LocalMemoryTracker:
    """Local memory-based token tracker for Redis failover."""
    
    def __init__(self):
        self.usage_data: Dict[str, List[TokenUsage]] = {}
        self.daily_totals: Dict[str, Dict[str, float]] = {}
        self.write_queue: deque[TokenUsage] = deque()
        
    async def track_usage(self, usage: TokenUsage) -> None:
        """Track usage in local memory."""
        if usage.user_id not in self.usage_data:
            self.usage_data[usage.user_id] = []
            
        self.usage_data[usage.user_id].append(usage)
        
        # Update daily totals
        today = usage.timestamp.date().isoformat()
        if today not in self.daily_totals:
            self.daily_totals[today] = {}
            
        if usage.user_id not in self.daily_totals[today]:
            self.daily_totals[today][usage.user_id] = 0.0
            
        self.daily_totals[today][usage.user_id] += usage.cost
        
        # Add to write queue for eventual sync
        self.write_queue.append(usage)
        
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics from local memory."""
        today = datetime.now().date().isoformat()
        
        # Calculate today's usage
        today_usage = 0.0
        if today in self.daily_totals and user_id in self.daily_totals[today]:
            today_usage = self.daily_totals[today][user_id]
            
        return {
            "today": {
                "used": today_usage,
                "remaining": 10.0 - today_usage,  # Default $10 daily limit
                "limit": 10.0
            },
            "total": {
                "used": sum(
                    usage.cost 
                    for usages in self.usage_data.values() 
                    for usage in usages 
                    if usage.user_id == user_id
                ),
                "count": len([
                    usage 
                    for usages in self.usage_data.values() 
                    for usage in usages 
                    if usage.user_id == user_id
                ])
            }
        }
        
    async def get_queued_data(self) -> List[TokenUsage]:
        """Get data queued for Redis sync."""
        return list(self.write_queue)
        
    async def clear_queue(self) -> None:
        """Clear the write queue after successful sync."""
        self.write_queue.clear()


class RedisTokenTracker:
    """Redis-based token tracker with persistence."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        
    async def connect(self) -> bool:
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            return False
            
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False
            
    async def track_usage(self, usage: TokenUsage) -> None:
        """Track usage in Redis."""
        if not self.redis_client:
            return
            
        try:
            # Store usage record
            key = f"usage:{usage.user_id}:{usage.timestamp.date().isoformat()}"
            # Convert to dict with datetime as ISO string
            usage_dict = asdict(usage)
            usage_dict['timestamp'] = usage.timestamp.isoformat()
            value = json.dumps(usage_dict)
            await self.redis_client.lpush(key, value)
            await self.redis_client.expire(key, 86400 * 30)  # 30 days
            
            # Update daily totals
            daily_key = f"daily:{usage.user_id}:{usage.timestamp.date().isoformat()}"
            await self.redis_client.hincrbyfloat(daily_key, "used", usage.cost)
            await self.redis_client.expire(daily_key, 86400 * 30)
            
            # Update user budget
            budget_key = f"budget:{usage.user_id}"
            await self.redis_client.hincrbyfloat(budget_key, "used_today", usage.cost)
            
        except Exception as e:
            logger.error(f"Failed to track usage in Redis: {e}")
            raise
            
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics from Redis."""
        if not self.redis_client:
            return {}
            
        try:
            today = datetime.now().date().isoformat()
            
            # Get daily usage
            daily_key = f"daily:{user_id}:{today}"
            daily_data = await self.redis_client.hgetall(daily_key)
            today_used = float(daily_data.get(b"used", 0))
            
            # Get budget info
            budget_key = f"budget:{user_id}"
            budget_data = await self.redis_client.hgetall(budget_key)
            daily_limit = float(budget_data.get(b"daily_limit", 10.0))
            
            return {
                "today": {
                    "used": today_used,
                    "remaining": daily_limit - today_used,
                    "limit": daily_limit
                },
                "total": {
                    "used": float(budget_data.get(b"used_total", 0)),
                    "count": int(budget_data.get(b"count_total", 0))
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats from Redis: {e}")
            return {}
            
    async def set_user_budget(self, user_id: str, daily_limit: float) -> None:
        """Set user daily budget."""
        if not self.redis_client:
            return
            
        try:
            budget_key = f"budget:{user_id}"
            await self.redis_client.hset(budget_key, "daily_limit", daily_limit)
            await self.redis_client.hset(budget_key, "used_today", 0)
            
        except Exception as e:
            logger.error(f"Failed to set user budget: {e}")


class ResilientTokenTracker:
    """
    Resilient token tracker with automatic failover.
    
    This tracker provides fault-tolerant token tracking that:
    1. Uses Redis when available for persistence
    2. Falls back to local memory when Redis is unavailable
    3. Automatically syncs queued data when Redis recovers
    4. Provides eventual consistency guarantees
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_tracker = RedisTokenTracker(redis_url)
        self.local_tracker = LocalMemoryTracker()
        self.use_redis = False
        self.sync_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> bool:
        """Initialize the tracker and determine Redis availability."""
        if REDIS_AVAILABLE:
            self.use_redis = await self.redis_tracker.connect()
            
        if self.use_redis:
            logger.info("Using Redis for token tracking")
            # Start background sync task
            self.sync_task = asyncio.create_task(self._sync_loop())
        else:
            logger.warning("Using local memory for token tracking")
            
        return self.use_redis
        
    async def track_usage(self, user_id: str, model: str, 
                         prompt_tokens: int, completion_tokens: int, 
                         cost: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Track token usage with automatic failover.
        
        Always succeeds, even if Redis is down. Data will be queued
        for eventual sync when Redis recovers.
        """
        usage = TokenUsage(
            user_id=user_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=cost,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # Always track in local memory for consistency
        await self.local_tracker.track_usage(usage)
        
        # Try Redis if available
        if self.use_redis:
            try:
                await self.redis_tracker.track_usage(usage)
            except Exception as e:
                logger.warning(f"Redis tracking failed, using local: {e}")
                self.use_redis = False
                # Will retry sync later
                
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics with automatic failover."""
        if self.use_redis:
            try:
                return await self.redis_tracker.get_user_stats(user_id)
            except Exception as e:
                logger.warning(f"Redis stats failed, using local: {e}")
                
        # Fallback to local memory
        return await self.local_tracker.get_user_stats(user_id)
        
    async def set_user_budget(self, user_id: str, daily_limit: float) -> None:
        """Set user daily budget with Redis fallback."""
        if self.use_redis:
            try:
                await self.redis_tracker.set_user_budget(user_id, daily_limit)
            except Exception as e:
                logger.warning(f"Redis budget set failed: {e}")
                
    async def _sync_loop(self):
        """Background task to sync queued data to Redis."""
        while True:
            try:
                if not self.use_redis:
                    # Try to reconnect to Redis
                    self.use_redis = await self.redis_tracker.connect()
                    if not self.use_redis:
                        await asyncio.sleep(30)
                        continue
                        
                # Sync queued data
                queued_data = await self.local_tracker.get_queued_data()
                if queued_data and self.use_redis:
                    logger.info(f"Syncing {len(queued_data)} queued usage records")
                    
                    for usage in queued_data:
                        try:
                            await self.redis_tracker.track_usage(usage)
                        except Exception as e:
                            logger.error(f"Failed to sync usage record: {e}")
                            break
                    else:
                        # All synced successfully
                        await self.local_tracker.clear_queue()
                        
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                self.use_redis = False
                
            await asyncio.sleep(30)  # Check every 30 seconds
            
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health information."""
        return {
            "redis_available": self.use_redis,
            "queued_records": len(await self.local_tracker.get_queued_data()),
            "local_memory_usage": len([
                usage 
                for usages in self.local_tracker.usage_data.values() 
                for usage in usages
            ])
        }
        
    async def close(self):
        """Clean up resources."""
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass


# Global instance
resilient_tracker = ResilientTokenTracker()
