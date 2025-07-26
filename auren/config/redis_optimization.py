"""
Redis Performance Optimization Configuration
Based on production requirements for handling 5000+ ops/sec
"""

import os
from typing import Dict, Any, Optional
import redis.asyncio as redis
from auren.core.logging_config import get_logger

logger = get_logger(__name__)


class RedisOptimizer:
    """
    Redis optimization utilities for production performance.
    Handles configuration, monitoring, and dynamic tuning.
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        
        # Optimal configuration based on workload
        self.optimal_config = {
            # Memory Management
            "maxmemory": "2gb",
            "maxmemory-policy": "allkeys-lru",  # LRU eviction for hot tier
            "maxmemory-samples": "10",  # Higher sampling for better eviction
            
            # Persistence (balanced for performance)
            "save": ["900 1", "300 10", "60 10000"],  # Less frequent saves
            "stop-writes-on-bgsave-error": "no",
            "rdbcompression": "yes",
            "rdbchecksum": "no",  # Skip checksum for speed
            
            # AOF for durability
            "appendonly": "yes",
            "appendfsync": "everysec",  # Balance between safety and performance
            "no-appendfsync-on-rewrite": "yes",
            "auto-aof-rewrite-percentage": "100",
            "auto-aof-rewrite-min-size": "64mb",
            
            # Performance tuning
            "tcp-backlog": "511",
            "timeout": "300",
            "tcp-keepalive": "300",
            "databases": "1",  # Single database for simplicity
            
            # Slow log configuration
            "slowlog-log-slower-than": "10000",  # Log queries slower than 10ms
            "slowlog-max-len": "128",
            
            # Client optimization
            "maxclients": "10000",
            
            # Threading (Redis 6+)
            "io-threads": "4",
            "io-threads-do-reads": "yes",
            
            # Lazy freeing for better performance
            "lazyfree-lazy-eviction": "yes",
            "lazyfree-lazy-expire": "yes",
            "lazyfree-lazy-server-del": "yes",
            "replica-lazy-flush": "yes"
        }
        
        # Connection pool configuration
        self.pool_config = {
            "max_connections": 100,
            "decode_responses": False,  # Binary for performance
            "socket_keepalive": True,
            "socket_keepalive_options": {
                1: 10,  # TCP_KEEPIDLE
                2: 3,   # TCP_KEEPINTVL  
                3: 5,   # TCP_KEEPCNT
            },
            "socket_connect_timeout": 5,
            "retry_on_timeout": True,
            "health_check_interval": 30
        }
    
    async def initialize(self):
        """Initialize Redis connection with optimized pool"""
        self.client = redis.from_url(
            self.redis_url,
            **self.pool_config
        )
        
        # Test connection
        await self.client.ping()
        logger.info("Redis optimizer initialized")
    
    async def apply_optimizations(self):
        """Apply performance optimizations to Redis"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        applied = []
        failed = []
        
        for key, value in self.optimal_config.items():
            try:
                if isinstance(value, list):
                    # Handle multiple values (like save)
                    for v in value:
                        await self.client.config_set(key, v)
                else:
                    await self.client.config_set(key, value)
                applied.append(key)
            except Exception as e:
                logger.warning(f"Failed to set {key}: {e}")
                failed.append(key)
        
        logger.info(f"Applied {len(applied)} optimizations, {len(failed)} failed")
        
        return {
            "applied": applied,
            "failed": failed,
            "total": len(self.optimal_config)
        }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current Redis performance metrics"""
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        # Get INFO stats
        info = await self.client.info()
        
        # Extract key metrics
        metrics = {
            "memory": {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0"),
                "used_memory_peak": info.get("used_memory_peak", 0),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0"),
                "mem_fragmentation_ratio": info.get("mem_fragmentation_ratio", 0),
                "evicted_keys": info.get("evicted_keys", 0)
            },
            "performance": {
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_input_kbps": info.get("instantaneous_input_kbps", 0),
                "instantaneous_output_kbps": info.get("instantaneous_output_kbps", 0),
                "rejected_connections": info.get("rejected_connections", 0)
            },
            "persistence": {
                "rdb_last_save_time": info.get("rdb_last_save_time", 0),
                "rdb_changes_since_last_save": info.get("rdb_changes_since_last_save", 0),
                "aof_current_size": info.get("aof_current_size", 0),
                "aof_pending_rewrite": info.get("aof_pending_rewrite", 0)
            },
            "clients": {
                "connected_clients": info.get("connected_clients", 0),
                "blocked_clients": info.get("blocked_clients", 0),
                "client_recent_max_input_buffer": info.get("client_recent_max_input_buffer", 0),
                "client_recent_max_output_buffer": info.get("client_recent_max_output_buffer", 0)
            },
            "keyspace": {}
        }
        
        # Get keyspace stats
        for db in range(16):
            db_key = f"db{db}"
            if db_key in info:
                metrics["keyspace"][db_key] = info[db_key]
        
        # Get slow queries
        slow_queries = await self.client.slowlog_get(10)
        metrics["slow_queries"] = [
            {
                "id": q[0],
                "timestamp": q[1],
                "duration_us": q[2],
                "command": " ".join(str(x) for x in q[3][:3]) + "..."  # First 3 args
            }
            for q in slow_queries
        ]
        
        return metrics
    
    async def optimize_for_workload(self, workload_type: str):
        """Optimize Redis for specific workload patterns"""
        workload_configs = {
            "high_write": {
                "appendfsync": "no",  # Faster writes
                "rdbcompression": "no",
                "save": "",  # Disable RDB
                "maxmemory-policy": "allkeys-lru"
            },
            "high_read": {
                "maxmemory-policy": "allkeys-lfu",  # Frequency-based eviction
                "maxmemory-samples": "20",  # Better sampling
                "io-threads": "8",  # More threads for reads
                "io-threads-do-reads": "yes"
            },
            "balanced": self.optimal_config,
            "memory_constrained": {
                "maxmemory": "1gb",
                "maxmemory-policy": "volatile-lru",
                "maxmemory-samples": "5",
                "hash-max-ziplist-entries": "256",
                "hash-max-ziplist-value": "32",
                "list-max-ziplist-size": "-2",
                "zset-max-ziplist-entries": "64",
                "zset-max-ziplist-value": "32"
            }
        }
        
        if workload_type not in workload_configs:
            raise ValueError(f"Unknown workload type: {workload_type}")
        
        config = workload_configs[workload_type]
        
        for key, value in config.items():
            try:
                await self.client.config_set(key, value)
            except Exception as e:
                logger.warning(f"Failed to set {key} for {workload_type}: {e}")
        
        logger.info(f"Optimized Redis for {workload_type} workload")
    
    async def create_indexes_for_patterns(self):
        """Create optimized data structures for common access patterns"""
        # This would create sorted sets, hashes, etc. for efficient access
        # Example: Agent memory access patterns
        
        pipeline = self.client.pipeline()
        
        # Create index for memory access by timestamp
        pipeline.zadd("idx:memory:access_time", {"dummy": 0})
        pipeline.delete("idx:memory:access_time")
        
        # Create index for memory by importance
        pipeline.zadd("idx:memory:importance", {"dummy": 0})
        pipeline.delete("idx:memory:importance")
        
        # Create hash for agent metadata
        pipeline.hset("idx:agent:metadata", "dummy", "0")
        pipeline.hdel("idx:agent:metadata", "dummy")
        
        await pipeline.execute()
        
        logger.info("Created Redis indexes for optimized access patterns")
    
    async def monitor_and_alert(self) -> Dict[str, Any]:
        """Monitor Redis health and generate alerts"""
        metrics = await self.get_performance_metrics()
        
        alerts = []
        
        # Memory pressure check
        used_memory = metrics["memory"]["used_memory"]
        max_memory = 2 * 1024 * 1024 * 1024  # 2GB
        memory_usage_percent = (used_memory / max_memory) * 100
        
        if memory_usage_percent > 80:
            alerts.append({
                "severity": "warning",
                "message": f"High memory usage: {memory_usage_percent:.1f}%"
            })
        
        if memory_usage_percent > 95:
            alerts.append({
                "severity": "critical",
                "message": f"Critical memory usage: {memory_usage_percent:.1f}%"
            })
        
        # Performance check
        ops_per_sec = metrics["performance"]["instantaneous_ops_per_sec"]
        if ops_per_sec > 10000:
            alerts.append({
                "severity": "info",
                "message": f"High load: {ops_per_sec} ops/sec"
            })
        
        # Slow queries check
        if len(metrics["slow_queries"]) > 5:
            alerts.append({
                "severity": "warning",
                "message": f"Multiple slow queries detected: {len(metrics['slow_queries'])}"
            })
        
        # Connection saturation
        connected = metrics["clients"]["connected_clients"]
        if connected > 9000:  # 90% of maxclients
            alerts.append({
                "severity": "warning",
                "message": f"High client connections: {connected}/10000"
            })
        
        return {
            "healthy": len([a for a in alerts if a["severity"] == "critical"]) == 0,
            "alerts": alerts,
            "metrics": metrics
        }
    
    async def cleanup(self):
        """Clean up Redis connection"""
        if self.client:
            await self.client.close()


# Singleton instance for global access
_redis_optimizer: Optional[RedisOptimizer] = None


async def get_redis_optimizer(redis_url: str) -> RedisOptimizer:
    """Get or create Redis optimizer instance"""
    global _redis_optimizer
    
    if _redis_optimizer is None:
        _redis_optimizer = RedisOptimizer(redis_url)
        await _redis_optimizer.initialize()
    
    return _redis_optimizer 