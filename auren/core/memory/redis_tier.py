"""
Redis Tier (Hot Memory) - Agent-Controlled Working Memory
Implements Tier 1 of the three-tier memory system with dynamic agent control
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
import redis.asyncio as redis
from redis.asyncio.lock import Lock
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class HotMemoryItem:
    """Memory item optimized for Redis storage with agent control"""
    memory_id: str
    agent_id: str
    user_id: str
    content: Dict[str, Any]
    memory_type: str
    confidence: float
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    priority: float = 1.0  # Agent-controlled priority
    ttl_override: Optional[int] = None  # Agent can override TTL
    metadata: Dict[str, Any] = None

    def to_redis_dict(self) -> Dict[str, str]:
        """Convert to Redis-compatible dictionary"""
        data = {
            'memory_id': self.memory_id,
            'agent_id': self.agent_id,
            'user_id': self.user_id,
            'content': json.dumps(self.content),
            'memory_type': self.memory_type,
            'confidence': str(self.confidence),
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': str(self.access_count),
            'priority': str(self.priority),
            'ttl_override': str(self.ttl_override) if self.ttl_override else '',
            'metadata': json.dumps(self.metadata or {})
        }
        return data

    @classmethod
    def from_redis_dict(cls, data: Dict[str, str]) -> 'HotMemoryItem':
        """Create from Redis data"""
        return cls(
            memory_id=data['memory_id'],
            agent_id=data['agent_id'],
            user_id=data['user_id'],
            content=json.loads(data['content']),
            memory_type=data['memory_type'],
            confidence=float(data['confidence']),
            created_at=datetime.fromisoformat(data['created_at']),
            last_accessed=datetime.fromisoformat(data['last_accessed']),
            access_count=int(data['access_count']),
            priority=float(data['priority']),
            ttl_override=int(data['ttl_override']) if data['ttl_override'] else None,
            metadata=json.loads(data['metadata'])
        )


class RedisTier:
    """
    Tier 1: Hot Memory with Agent Control
    
    Features:
    - Sub-10ms access times
    - Agent-controlled priority and TTL
    - Automatic memory pressure management
    - Pattern-based access tracking
    - WebSocket event emission
    """
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 default_ttl_days: int = 30,
                 max_memory_items: int = 10000,
                 event_emitter=None):
        self.redis_url = redis_url
        self.default_ttl = timedelta(days=default_ttl_days)
        self.max_memory_items = max_memory_items
        self.event_emitter = event_emitter
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False
        
        # Key patterns
        self.MEMORY_KEY = "memory:{memory_id}"
        self.USER_MEMORIES = "user:{user_id}:memories"
        self.AGENT_MEMORIES = "agent:{agent_id}:memories"
        self.ACCESS_PATTERN = "access:{user_id}:{pattern}"
        self.PRIORITY_INDEX = "priority:index"
        self.AGENT_CONTROL = "agent:{agent_id}:control"
    
    async def connect(self):
        """Establish Redis connection"""
        if not self._connected:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self._connected = True
            logger.info("Redis tier connected successfully")
            
            # Verify connection
            await self.redis_client.ping()
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._connected and self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Redis tier disconnected")
    
    async def store_memory(self, 
                          memory_id: str,
                          agent_id: str,
                          user_id: str,
                          content: Dict[str, Any],
                          memory_type: str,
                          confidence: float = 1.0,
                          priority: float = 1.0,
                          ttl_override: Optional[int] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store memory in hot tier with agent control
        
        Args:
            memory_id: Unique memory identifier
            agent_id: Agent storing the memory
            user_id: Associated user
            content: Memory content
            memory_type: Type of memory
            confidence: Confidence score
            priority: Agent-assigned priority (higher = keep longer)
            ttl_override: Agent override for TTL in seconds
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        if not self._connected:
            await self.connect()
        
        try:
            memory = HotMemoryItem(
                memory_id=memory_id,
                agent_id=agent_id,
                user_id=user_id,
                content=content,
                memory_type=memory_type,
                confidence=confidence,
                created_at=datetime.now(timezone.utc),
                last_accessed=datetime.now(timezone.utc),
                priority=priority,
                ttl_override=ttl_override,
                metadata=metadata
            )
            
            # Store memory data
            memory_key = self.MEMORY_KEY.format(memory_id=memory_id)
            pipe = self.redis_client.pipeline()
            
            # Set memory data
            pipe.hset(memory_key, mapping=memory.to_redis_dict())
            
            # Set TTL based on agent preference or default
            ttl = ttl_override if ttl_override else int(self.default_ttl.total_seconds())
            pipe.expire(memory_key, ttl)
            
            # Add to indices
            pipe.sadd(self.USER_MEMORIES.format(user_id=user_id), memory_id)
            pipe.sadd(self.AGENT_MEMORIES.format(agent_id=agent_id), memory_id)
            
            # Add to priority index for memory pressure management
            pipe.zadd(self.PRIORITY_INDEX, {memory_id: priority})
            
            # Execute pipeline
            await pipe.execute()
            
            # Emit event if configured
            if self.event_emitter:
                await self._emit_memory_event('memory_stored', memory)
            
            # Check memory pressure
            await self._manage_memory_pressure()
            
            logger.debug(f"Stored memory {memory_id} in Redis tier")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory {memory_id}: {e}")
            return False
    
    async def retrieve_memory(self, memory_id: str) -> Optional[HotMemoryItem]:
        """
        Retrieve memory with access tracking
        
        Args:
            memory_id: Memory to retrieve
            
        Returns:
            Memory item or None
        """
        if not self._connected:
            await self.connect()
        
        try:
            memory_key = self.MEMORY_KEY.format(memory_id=memory_id)
            
            # Get memory data
            data = await self.redis_client.hgetall(memory_key)
            if not data:
                return None
            
            # Update access tracking
            pipe = self.redis_client.pipeline()
            pipe.hincrby(memory_key, 'access_count', 1)
            pipe.hset(memory_key, 'last_accessed', datetime.now(timezone.utc).isoformat())
            
            # Refresh TTL on access
            current_ttl = await self.redis_client.ttl(memory_key)
            if current_ttl > 0:
                pipe.expire(memory_key, current_ttl)
            
            await pipe.execute()
            
            # Parse and return
            memory = HotMemoryItem.from_redis_dict(data)
            
            # Track access pattern
            await self._track_access_pattern(memory)
            
            return memory
            
        except Exception as e:
            logger.error(f"Failed to retrieve memory {memory_id}: {e}")
            return None
    
    async def get_user_memories(self, 
                               user_id: str,
                               memory_type: Optional[str] = None,
                               limit: int = 100) -> List[HotMemoryItem]:
        """Get all memories for a user"""
        if not self._connected:
            await self.connect()
        
        try:
            # Get memory IDs for user
            memory_ids = await self.redis_client.smembers(
                self.USER_MEMORIES.format(user_id=user_id)
            )
            
            memories = []
            for memory_id in memory_ids:
                memory = await self.retrieve_memory(memory_id)
                if memory and (not memory_type or memory.memory_type == memory_type):
                    memories.append(memory)
            
            # Sort by priority and recency
            memories.sort(
                key=lambda m: (m.priority, m.last_accessed),
                reverse=True
            )
            
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get user memories: {e}")
            return []
    
    async def update_memory_priority(self, 
                                   memory_id: str,
                                   agent_id: str,
                                   new_priority: float,
                                   new_ttl: Optional[int] = None) -> bool:
        """
        Allow agent to update memory priority and TTL
        
        Args:
            memory_id: Memory to update
            agent_id: Agent requesting update
            new_priority: New priority value
            new_ttl: New TTL in seconds (optional)
            
        Returns:
            Success status
        """
        if not self._connected:
            await self.connect()
        
        try:
            memory_key = self.MEMORY_KEY.format(memory_id=memory_id)
            
            # Verify agent owns this memory
            stored_agent_id = await self.redis_client.hget(memory_key, 'agent_id')
            if stored_agent_id != agent_id:
                logger.warning(f"Agent {agent_id} cannot update memory owned by {stored_agent_id}")
                return False
            
            # Update priority
            pipe = self.redis_client.pipeline()
            pipe.hset(memory_key, 'priority', str(new_priority))
            pipe.zadd(self.PRIORITY_INDEX, {memory_id: new_priority})
            
            # Update TTL if provided
            if new_ttl:
                pipe.hset(memory_key, 'ttl_override', str(new_ttl))
                pipe.expire(memory_key, new_ttl)
            
            await pipe.execute()
            
            # Log agent control action
            await self._log_agent_control(agent_id, memory_id, 'priority_update', {
                'new_priority': new_priority,
                'new_ttl': new_ttl
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update memory priority: {e}")
            return False
    
    async def get_memory_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get memory statistics"""
        if not self._connected:
            await self.connect()
        
        try:
            # Get total memory count
            total_memories = await self.redis_client.zcard(self.PRIORITY_INDEX)
            
            # Get user-specific stats if requested
            user_memories = 0
            if user_id:
                user_memory_ids = await self.redis_client.smembers(
                    self.USER_MEMORIES.format(user_id=user_id)
                )
                user_memories = len(user_memory_ids)
            
            # Get memory pressure info
            memory_info = await self.redis_client.memory_stats()
            used_memory = memory_info.get('used_memory', 0)
            
            # Get access patterns
            pattern_keys = await self.redis_client.keys(self.ACCESS_PATTERN.format(
                user_id=user_id or '*',
                pattern='*'
            ))
            
            stats = {
                'total_memories': total_memories,
                'user_memories': user_memories,
                'memory_pressure': total_memories / self.max_memory_items,
                'used_memory_mb': used_memory / (1024 * 1024),
                'access_patterns': len(pattern_keys),
                'max_capacity': self.max_memory_items
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    async def _manage_memory_pressure(self):
        """Manage memory pressure by evicting low-priority memories"""
        try:
            total_memories = await self.redis_client.zcard(self.PRIORITY_INDEX)
            
            if total_memories > self.max_memory_items:
                # Calculate how many to evict
                to_evict = int((total_memories - self.max_memory_items) * 1.1)  # 10% buffer
                
                # Get lowest priority memories
                low_priority_memories = await self.redis_client.zrange(
                    self.PRIORITY_INDEX, 0, to_evict - 1
                )
                
                # Evict memories
                pipe = self.redis_client.pipeline()
                for memory_id in low_priority_memories:
                    memory_key = self.MEMORY_KEY.format(memory_id=memory_id)
                    
                    # Get memory data before deletion
                    memory_data = await self.redis_client.hgetall(memory_key)
                    if memory_data:
                        # Emit eviction event
                        if self.event_emitter:
                            await self._emit_memory_event('memory_evicted', {
                                'memory_id': memory_id,
                                'reason': 'memory_pressure',
                                'priority': memory_data.get('priority', 0)
                            })
                    
                    # Delete memory
                    pipe.delete(memory_key)
                    pipe.zrem(self.PRIORITY_INDEX, memory_id)
                    
                    # Remove from indices
                    user_id = memory_data.get('user_id')
                    agent_id = memory_data.get('agent_id')
                    if user_id:
                        pipe.srem(self.USER_MEMORIES.format(user_id=user_id), memory_id)
                    if agent_id:
                        pipe.srem(self.AGENT_MEMORIES.format(agent_id=agent_id), memory_id)
                
                await pipe.execute()
                logger.info(f"Evicted {to_evict} memories due to memory pressure")
                
        except Exception as e:
            logger.error(f"Failed to manage memory pressure: {e}")
    
    async def _track_access_pattern(self, memory: HotMemoryItem):
        """Track memory access patterns for optimization"""
        try:
            # Create pattern key based on memory type and time
            hour = datetime.now(timezone.utc).hour
            pattern = f"{memory.memory_type}:hour_{hour}"
            pattern_key = self.ACCESS_PATTERN.format(
                user_id=memory.user_id,
                pattern=pattern
            )
            
            # Increment pattern counter
            await self.redis_client.hincrby(pattern_key, 'count', 1)
            await self.redis_client.hset(pattern_key, 'last_access', 
                                       datetime.now(timezone.utc).isoformat())
            
            # Expire pattern data after 7 days
            await self.redis_client.expire(pattern_key, 7 * 24 * 60 * 60)
            
        except Exception as e:
            logger.error(f"Failed to track access pattern: {e}")
    
    async def _log_agent_control(self, agent_id: str, memory_id: str, 
                                action: str, details: Dict[str, Any]):
        """Log agent control actions for audit"""
        try:
            control_key = self.AGENT_CONTROL.format(agent_id=agent_id)
            log_entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'memory_id': memory_id,
                'action': action,
                'details': details
            }
            
            # Store as list in Redis
            await self.redis_client.lpush(control_key, json.dumps(log_entry))
            await self.redis_client.ltrim(control_key, 0, 999)  # Keep last 1000 actions
            await self.redis_client.expire(control_key, 30 * 24 * 60 * 60)  # 30 days
            
        except Exception as e:
            logger.error(f"Failed to log agent control: {e}")
    
    async def _emit_memory_event(self, event_type: str, data: Any):
        """Emit memory event for dashboard"""
        if self.event_emitter:
            try:
                await self.event_emitter.emit({
                    'type': f'redis_tier_{event_type}',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'data': data if isinstance(data, dict) else asdict(data)
                })
            except Exception as e:
                logger.error(f"Failed to emit event: {e}")
    
    async def agent_decide_retention(self, agent_id: str, 
                                   criteria: Dict[str, Any]) -> List[str]:
        """
        Let agent decide which memories to retain based on criteria
        
        Args:
            agent_id: Agent making decision
            criteria: Decision criteria (e.g., importance, recency, relevance)
            
        Returns:
            List of memory IDs to retain
        """
        if not self._connected:
            await self.connect()
        
        try:
            # Get agent's memories
            memory_ids = await self.redis_client.smembers(
                self.AGENT_MEMORIES.format(agent_id=agent_id)
            )
            
            memories_to_evaluate = []
            for memory_id in memory_ids:
                memory = await self.retrieve_memory(memory_id)
                if memory:
                    memories_to_evaluate.append(memory)
            
            # Apply agent criteria
            retained_memories = []
            for memory in memories_to_evaluate:
                score = 0.0
                
                # Importance criterion
                if 'min_confidence' in criteria:
                    if memory.confidence >= criteria['min_confidence']:
                        score += 1.0
                
                # Recency criterion
                if 'max_age_days' in criteria:
                    age = (datetime.now(timezone.utc) - memory.created_at).days
                    if age <= criteria['max_age_days']:
                        score += 1.0
                
                # Access frequency criterion
                if 'min_access_count' in criteria:
                    if memory.access_count >= criteria['min_access_count']:
                        score += 1.0
                
                # Priority criterion
                if 'min_priority' in criteria:
                    if memory.priority >= criteria['min_priority']:
                        score += 1.0
                
                # Retain if score meets threshold
                threshold = criteria.get('score_threshold', 2.0)
                if score >= threshold:
                    retained_memories.append(memory.memory_id)
                    
                    # Update priority for retained memories
                    new_priority = min(memory.priority * 1.5, 10.0)  # Boost priority
                    await self.update_memory_priority(
                        memory.memory_id, agent_id, new_priority
                    )
            
            # Log retention decision
            await self._log_agent_control(agent_id, 'batch', 'retention_decision', {
                'total_evaluated': len(memories_to_evaluate),
                'retained': len(retained_memories),
                'criteria': criteria
            })
            
            return retained_memories
            
        except Exception as e:
            logger.error(f"Failed in agent retention decision: {e}")
            return [] 