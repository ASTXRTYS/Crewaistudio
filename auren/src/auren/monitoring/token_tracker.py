"""
AUREN Token Tracking System - Core Implementation
Tracks token usage, costs, and enforces budget limits in real-time
"""

import asyncio
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Optional, Tuple, Any
from redis import asyncio as aioredis
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage data for a single LLM call"""
    request_id: str
    user_id: str
    agent_id: str
    task_id: str
    conversation_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    timestamp: str
    metadata: Dict[str, Any] = None

    def to_dict(self) -> dict:
        return asdict(self)


class TokenTracker:
    """
    Production-grade token tracking with Redis backend
    Handles real-time usage tracking, budget enforcement, and cost analytics
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
        self._lock = asyncio.Lock()
        
        # Model pricing (per 1K tokens) - Update these with current prices
        self.model_pricing = {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
            "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
            "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
            "llama-3.1-70b": {"prompt": 0.00266, "completion": 0.00354},  # Self-hosted
        }
        
        # Default daily limits (in USD)
        self.default_daily_limit = 10.0
        self.default_warning_threshold = 0.8  # 80% warning
        
    async def connect(self):
        """Establish Redis connection"""
        if not self._redis:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis for token tracking")
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost in USD for token usage"""
        if model not in self.model_pricing:
            logger.warning(f"Unknown model {model}, using GPT-3.5 pricing")
            model = "gpt-3.5-turbo"
        
        pricing = self.model_pricing[model]
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        
        return round(prompt_cost + completion_cost, 6)
    
    async def track_usage(
        self,
        user_id: str,
        agent_id: str,
        task_id: str,
        conversation_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TokenUsage:
        """
        Track token usage for a single LLM call
        
        Returns:
            TokenUsage object with all tracking data
        
        Raises:
            BudgetExceededException if user exceeds daily limit
        """
        if not self._redis:
            await self.connect()
        
        # Create usage record
        usage = TokenUsage(
            request_id=str(uuid.uuid4()),
            user_id=user_id,
            agent_id=agent_id,
            task_id=task_id,
            conversation_id=conversation_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=self._calculate_cost(model, prompt_tokens, completion_tokens),
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )
        
        # Check budget before tracking
        await self._check_budget(user_id, usage.cost_usd)
        
        # Track in Redis with atomic operations
        async with self._lock:
            await self._track_in_redis(usage)
        
        # Log for debugging
        logger.info(
            f"Tracked {usage.total_tokens} tokens for user={user_id}, "
            f"agent={agent_id}, cost=${usage.cost_usd:.4f}"
        )
        
        return usage
    
    async def _track_in_redis(self, usage: TokenUsage):
        """Store usage data in Redis with multiple indexes"""
        pipe = self._redis.pipeline()
        
        # 1. Store full usage record (24hr TTL)
        usage_key = f"usage:{usage.request_id}"
        pipe.hset(usage_key, mapping=usage.to_dict())
        pipe.expire(usage_key, 86400)  # 24 hours
        
        # 2. Update daily user totals
        today = date.today().isoformat()
        daily_key = f"daily:{usage.user_id}:{today}"
        pipe.hincrbyfloat(daily_key, "total_cost", usage.cost_usd)
        pipe.hincrby(daily_key, "total_tokens", usage.total_tokens)
        pipe.hincrby(daily_key, "request_count", 1)
        pipe.expire(daily_key, 172800)  # 48 hours
        
        # 3. Update hourly metrics for monitoring
        hour = datetime.utcnow().strftime("%Y-%m-%d:%H")
        hourly_key = f"hourly:{hour}"
        pipe.hincrbyfloat(hourly_key, "cost", usage.cost_usd)
        pipe.hincrby(hourly_key, "tokens", usage.total_tokens)
        pipe.expire(hourly_key, 3600)  # 1 hour
        
        # 4. Track by agent for cost attribution
        agent_key = f"agent:{usage.agent_id}:{today}"
        pipe.hincrbyfloat(agent_key, "cost", usage.cost_usd)
        pipe.hincrby(agent_key, "tokens", usage.total_tokens)
        pipe.expire(agent_key, 172800)
        
        # 5. Add to conversation history
        conv_key = f"conversation:{usage.conversation_id}"
        pipe.lpush(conv_key, usage.request_id)
        pipe.ltrim(conv_key, 0, 99)  # Keep last 100
        pipe.expire(conv_key, 7200)  # 2 hours
        
        await pipe.execute()
    
    async def _check_budget(self, user_id: str, cost: float):
        """Check if user has budget remaining"""
        today = date.today().isoformat()
        daily_key = f"daily:{user_id}:{today}"
        
        # Get current spending
        current_cost = await self._redis.hget(daily_key, "total_cost") or "0"
        current_cost = float(current_cost)
        
        # Get user's limit (could be custom per user)
        limit_key = f"limit:{user_id}"
        user_limit = await self._redis.get(limit_key)
        limit = float(user_limit) if user_limit else self.default_daily_limit
        
        # Check if over budget
        if current_cost + cost > limit:
            raise BudgetExceededException(
                f"User {user_id} would exceed daily limit of ${limit:.2f}. "
                f"Current: ${current_cost:.2f}, Requested: ${cost:.4f}"
            )
        
        # Check warning threshold
        if current_cost + cost > limit * self.default_warning_threshold:
            logger.warning(
                f"User {user_id} approaching limit: ${current_cost + cost:.2f} / ${limit:.2f}"
            )
    
    async def get_user_stats(self, user_id: str, days: int = 1) -> Dict[str, Any]:
        """Get usage statistics for a user"""
        stats = {
            "user_id": user_id,
            "daily_breakdown": []
        }
        
        for i in range(days):
            day = (date.today() - timedelta(days=i)).isoformat()
            daily_key = f"daily:{user_id}:{day}"
            
            data = await self._redis.hgetall(daily_key)
            if data:
                stats["daily_breakdown"].append({
                    "date": day,
                    "total_cost": float(data.get("total_cost", 0)),
                    "total_tokens": int(data.get("total_tokens", 0)),
                    "request_count": int(data.get("request_count", 0))
                })
        
        # Current day spending
        today_data = stats["daily_breakdown"][0] if stats["daily_breakdown"] else {}
        limit_key = f"limit:{user_id}"
        user_limit = await self._redis.get(limit_key)
        limit = float(user_limit) if user_limit else self.default_daily_limit
        
        stats["today"] = {
            "spent": today_data.get("total_cost", 0),
            "limit": limit,
            "remaining": limit - today_data.get("total_cost", 0),
            "percentage": (today_data.get("total_cost", 0) / limit * 100) if limit > 0 else 0
        }
        
        return stats
    
    async def set_user_limit(self, user_id: str, daily_limit_usd: float, admin_id: str = None):
        """Set custom daily limit for a user"""
        limit_key = f"limit:{user_id}"
        await self._redis.set(limit_key, daily_limit_usd)
        
        # Audit log
        audit_entry = {
            "action": "set_limit",
            "user_id": user_id,
            "new_limit": daily_limit_usd,
            "admin_id": admin_id or "system",
            "timestamp": datetime.utcnow().isoformat()
        }
        audit_key = f"audit:limits:{datetime.utcnow().strftime('%Y-%m-%d')}"
        await self._redis.lpush(audit_key, json.dumps(audit_entry))
        await self._redis.expire(audit_key, 2592000)  # 30 days
        
        logger.info(f"Set daily limit for {user_id} to ${daily_limit_usd} by {admin_id or 'system'}")


class BudgetExceededException(Exception):
    """Raised when a user exceeds their token budget"""
    pass
