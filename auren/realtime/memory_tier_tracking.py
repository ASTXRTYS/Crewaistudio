"""
Memory Tier Tracking for AUREN
Tracks memory access patterns across Redis, PostgreSQL, and ChromaDB tiers
Provides detailed metrics on cache effectiveness and latency
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
import json
import redis.asyncio as redis
import asyncpg
from collections import defaultdict, deque
import numpy as np

logger = logging.getLogger(__name__)

class MemoryTier(Enum):
    """Memory storage tiers in order of access speed"""
    REDIS = "redis"           # Tier 1: Immediate cache (ms latency)
    POSTGRESQL = "postgresql"  # Tier 2: Structured storage (10s ms latency)
    CHROMADB = "chromadb"     # Tier 3: Vector/semantic storage (100s ms latency)

@dataclass
class TierAccessMetrics:
    """Metrics for a single tier access"""
    tier: MemoryTier
    hit: bool
    latency_ms: float
    items_found: int
    timestamp: datetime
    query_type: str
    query_complexity: str

@dataclass
class TierPerformanceStats:
    """Aggregated performance statistics for a tier"""
    tier: MemoryTier
    total_accesses: int
    hits: int
    misses: int
    hit_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    items_served: int
    last_updated: datetime

class MemoryTierTracker:
    """
    Tracks memory access patterns across all tiers
    Provides real-time metrics and optimization recommendations
    """
    
    def __init__(self, 
                 event_streamer=None,
                 metrics_window_size: int = 1000,
                 stats_update_interval: int = 60):
        self.event_streamer = event_streamer
        self.metrics_window_size = metrics_window_size
        self.stats_update_interval = stats_update_interval
        
        # Metrics storage per tier
        self.tier_metrics = {
            MemoryTier.REDIS: deque(maxlen=metrics_window_size),
            MemoryTier.POSTGRESQL: deque(maxlen=metrics_window_size),
            MemoryTier.CHROMADB: deque(maxlen=metrics_window_size)
        }
        
        # Aggregated statistics
        self.tier_stats = {}
        self.last_stats_update = datetime.now(timezone.utc)
        
        # Query pattern tracking
        self.query_patterns = defaultdict(lambda: {
            'count': 0,
            'avg_latency': 0,
            'tier_distribution': defaultdict(int)
        })
        
        # Cache effectiveness tracking
        self.cache_chains = []  # Track full lookup chains
        self.optimization_candidates = []
        
        # Real-time performance tracking
        self.current_hour_stats = {
            'accesses': 0,
            'cache_hits': 0,
            'total_latency': 0,
            'tier_costs': defaultdict(float)
        }
        
        # Cost model (example values)
        self.tier_costs = {
            MemoryTier.REDIS: 0.0001,      # $0.0001 per access
            MemoryTier.POSTGRESQL: 0.001,   # $0.001 per access
            MemoryTier.CHROMADB: 0.01      # $0.01 per access (vector search)
        }
    
    async def track_memory_access(self,
                                  query: str,
                                  user_id: Optional[str] = None,
                                  agent_id: Optional[str] = None) -> Tuple[Any, Dict[str, Any]]:
        """
        Track a complete memory access across all tiers
        Returns the result and detailed access metrics
        """
        
        access_chain = []
        result = None
        total_start = time.time()
        
        # Determine query complexity
        query_complexity = self._assess_query_complexity(query)
        query_type = self._classify_query_type(query)
        
        # Try Redis first (Tier 1)
        redis_start = time.time()
        redis_result = await self._try_redis_tier(query, user_id)
        redis_latency = (time.time() - redis_start) * 1000
        
        redis_metrics = TierAccessMetrics(
            tier=MemoryTier.REDIS,
            hit=redis_result is not None,
            latency_ms=redis_latency,
            items_found=len(redis_result) if redis_result else 0,
            timestamp=datetime.now(timezone.utc),
            query_type=query_type,
            query_complexity=query_complexity
        )
        access_chain.append(redis_metrics)
        self.tier_metrics[MemoryTier.REDIS].append(redis_metrics)
        
        if redis_result:
            result = redis_result
        else:
            # Try PostgreSQL (Tier 2)
            pg_start = time.time()
            pg_result = await self._try_postgresql_tier(query, user_id)
            pg_latency = (time.time() - pg_start) * 1000
            
            pg_metrics = TierAccessMetrics(
                tier=MemoryTier.POSTGRESQL,
                hit=pg_result is not None,
                latency_ms=pg_latency,
                items_found=len(pg_result) if pg_result else 0,
                timestamp=datetime.now(timezone.utc),
                query_type=query_type,
                query_complexity=query_complexity
            )
            access_chain.append(pg_metrics)
            self.tier_metrics[MemoryTier.POSTGRESQL].append(pg_metrics)
            
            if pg_result:
                result = pg_result
                # Potentially cache in Redis for next time
                await self._cache_in_redis(query, pg_result, user_id)
            else:
                # Try ChromaDB (Tier 3)
                chroma_start = time.time()
                chroma_result = await self._try_chromadb_tier(query, user_id)
                chroma_latency = (time.time() - chroma_start) * 1000
                
                chroma_metrics = TierAccessMetrics(
                    tier=MemoryTier.CHROMADB,
                    hit=chroma_result is not None,
                    latency_ms=chroma_latency,
                    items_found=len(chroma_result) if chroma_result else 0,
                    timestamp=datetime.now(timezone.utc),
                    query_type=query_type,
                    query_complexity=query_complexity
                )
                access_chain.append(chroma_metrics)
                self.tier_metrics[MemoryTier.CHROMADB].append(chroma_metrics)
                
                if chroma_result:
                    result = chroma_result
                    # Cache in both Redis and PostgreSQL
                    await self._cache_in_redis(query, chroma_result, user_id)
                    await self._cache_in_postgresql(query, chroma_result, user_id)
        
        # Calculate total metrics
        total_latency = (time.time() - total_start) * 1000
        tier_accessed = self._determine_serving_tier(access_chain)
        
        # Update statistics
        self._update_current_stats(access_chain, total_latency)
        self._update_query_patterns(query, access_chain)
        self.cache_chains.append(access_chain)
        
        # Emit memory tier access event
        if self.event_streamer:
            await self._emit_tier_access_event(
                query=query,
                user_id=user_id,
                agent_id=agent_id,
                access_chain=access_chain,
                tier_accessed=tier_accessed,
                total_latency=total_latency,
                result_count=len(result) if result else 0
            )
        
        # Check if we need to update aggregated stats
        if self._should_update_stats():
            await self._update_tier_statistics()
        
        # Analyze for optimization opportunities
        self._analyze_optimization_opportunities(query, access_chain)
        
        return result, {
            'tier_accessed': tier_accessed.value,
            'total_latency_ms': total_latency,
            'access_chain': [asdict(m) for m in access_chain],
            'cache_effectiveness': self.calculate_cache_effectiveness(),
            'optimization_suggestions': self.get_optimization_suggestions()
        }
    
    async def _try_redis_tier(self, query: str, user_id: Optional[str]) -> Optional[List[Dict]]:
        """Attempt to retrieve from Redis tier"""
        # Mock implementation - replace with actual Redis access
        await asyncio.sleep(0.005)  # Simulate 5ms Redis latency
        
        # Simulate 45% hit rate for Redis
        import random
        if random.random() < 0.45:
            return [{"source": "redis", "data": f"cached_{query}"}]
        return None
    
    async def _try_postgresql_tier(self, query: str, user_id: Optional[str]) -> Optional[List[Dict]]:
        """Attempt to retrieve from PostgreSQL tier"""
        # Mock implementation - replace with actual PostgreSQL access
        await asyncio.sleep(0.025)  # Simulate 25ms PostgreSQL latency
        
        # Simulate 85% hit rate for PostgreSQL (if Redis missed)
        import random
        if random.random() < 0.85:
            return [{"source": "postgresql", "data": f"structured_{query}"}]
        return None
    
    async def _try_chromadb_tier(self, query: str, user_id: Optional[str]) -> Optional[List[Dict]]:
        """Attempt to retrieve from ChromaDB tier"""
        # Mock implementation - replace with actual ChromaDB access
        await asyncio.sleep(0.150)  # Simulate 150ms ChromaDB latency
        
        # ChromaDB always returns something (semantic search)
        return [{"source": "chromadb", "data": f"semantic_{query}", "similarity": 0.85}]
    
    async def _cache_in_redis(self, query: str, data: List[Dict], user_id: Optional[str]):
        """Cache data in Redis for future access"""
        # Mock implementation
        logger.debug(f"Caching {len(data)} items in Redis for query: {query}")
    
    async def _cache_in_postgresql(self, query: str, data: List[Dict], user_id: Optional[str]):
        """Cache data in PostgreSQL for future access"""
        # Mock implementation
        logger.debug(f"Caching {len(data)} items in PostgreSQL for query: {query}")
    
    def _assess_query_complexity(self, query: str) -> str:
        """Assess the complexity of a query"""
        if len(query) < 20:
            return "simple"
        elif len(query) < 100:
            return "moderate"
        else:
            return "complex"
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query"""
        query_lower = query.lower()
        
        if any(term in query_lower for term in ['hrv', 'heart', 'biometric']):
            return "biometric"
        elif any(term in query_lower for term in ['hypothesis', 'pattern', 'correlation']):
            return "analytical"
        elif any(term in query_lower for term in ['history', 'previous', 'past']):
            return "historical"
        elif any(term in query_lower for term in ['knowledge', 'fact', 'information']):
            return "knowledge"
        else:
            return "general"
    
    def _determine_serving_tier(self, access_chain: List[TierAccessMetrics]) -> MemoryTier:
        """Determine which tier ultimately served the request"""
        for metrics in access_chain:
            if metrics.hit:
                return metrics.tier
        return MemoryTier.CHROMADB  # Default if nothing hit
    
    def _update_current_stats(self, access_chain: List[TierAccessMetrics], total_latency: float):
        """Update current hour statistics"""
        self.current_hour_stats['accesses'] += 1
        self.current_hour_stats['total_latency'] += total_latency
        
        # Count cache hit (Redis hit)
        if access_chain[0].hit:
            self.current_hour_stats['cache_hits'] += 1
        
        # Calculate tier costs
        for metrics in access_chain:
            cost = self.tier_costs[metrics.tier]
            self.current_hour_stats['tier_costs'][metrics.tier] += cost
    
    def _update_query_patterns(self, query: str, access_chain: List[TierAccessMetrics]):
        """Update query pattern tracking"""
        pattern_key = self._extract_pattern_key(query)
        pattern = self.query_patterns[pattern_key]
        
        pattern['count'] += 1
        total_latency = sum(m.latency_ms for m in access_chain)
        pattern['avg_latency'] = (pattern['avg_latency'] * (pattern['count'] - 1) + total_latency) / pattern['count']
        
        serving_tier = self._determine_serving_tier(access_chain)
        pattern['tier_distribution'][serving_tier.value] += 1
    
    def _extract_pattern_key(self, query: str) -> str:
        """Extract a pattern key from query for grouping similar queries"""
        # Simple implementation - in practice would use more sophisticated parsing
        words = query.lower().split()[:3]  # First 3 words
        return " ".join(words)
    
    def _should_update_stats(self) -> bool:
        """Check if it's time to update aggregated statistics"""
        time_since_update = (datetime.now(timezone.utc) - self.last_stats_update).total_seconds()
        return time_since_update >= self.stats_update_interval
    
    async def _update_tier_statistics(self):
        """Update aggregated tier statistics"""
        self.last_stats_update = datetime.now(timezone.utc)
        
        for tier in MemoryTier:
            metrics_list = list(self.tier_metrics[tier])
            if not metrics_list:
                continue
            
            hits = sum(1 for m in metrics_list if m.hit)
            total = len(metrics_list)
            latencies = [m.latency_ms for m in metrics_list]
            
            self.tier_stats[tier] = TierPerformanceStats(
                tier=tier,
                total_accesses=total,
                hits=hits,
                misses=total - hits,
                hit_rate=hits / total if total > 0 else 0,
                avg_latency_ms=np.mean(latencies) if latencies else 0,
                p95_latency_ms=np.percentile(latencies, 95) if latencies else 0,
                p99_latency_ms=np.percentile(latencies, 99) if latencies else 0,
                items_served=sum(m.items_found for m in metrics_list if m.hit),
                last_updated=self.last_stats_update
            )
    
    def _analyze_optimization_opportunities(self, query: str, access_chain: List[TierAccessMetrics]):
        """Analyze access patterns for optimization opportunities"""
        
        # If we had to go to ChromaDB, consider caching more aggressively
        if len(access_chain) >= 3 and access_chain[-1].hit:
            pattern_key = self._extract_pattern_key(query)
            pattern = self.query_patterns[pattern_key]
            
            # If this pattern is frequent and slow, suggest optimization
            if pattern['count'] > 10 and pattern['avg_latency'] > 100:
                self.optimization_candidates.append({
                    'pattern': pattern_key,
                    'frequency': pattern['count'],
                    'avg_latency': pattern['avg_latency'],
                    'suggestion': 'Pre-cache this query pattern in Redis',
                    'potential_savings_ms': pattern['avg_latency'] - 5  # Redis latency
                })
    
    async def _emit_tier_access_event(self, **kwargs):
        """Emit a memory tier access event"""
        if not self.event_streamer:
            return
        
        from auren.realtime.crewai_instrumentation import AURENStreamEvent, AURENEventType
        
        # Build tier latency breakdown
        tier_latencies = {}
        for metrics in kwargs['access_chain']:
            tier_latencies[metrics.tier.value] = {
                'latency_ms': metrics.latency_ms,
                'hit': metrics.hit,
                'items_found': metrics.items_found
            }
        
        event = AURENStreamEvent(
            event_id=f"mem_tier_{datetime.now().timestamp()}",
            trace_id=kwargs.get('trace_id'),
            session_id=kwargs.get('session_id'),
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.MEMORY_TIER_ACCESS,
            source_agent={"id": kwargs.get('agent_id', 'memory_system')},
            target_agent=None,
            payload={
                'query': kwargs['query'][:100],  # Truncate for dashboard
                'tier_accessed': kwargs['tier_accessed'].value,
                'tier_latencies': tier_latencies,
                'total_latency_ms': kwargs['total_latency'],
                'result_count': kwargs['result_count'],
                'query_type': kwargs['access_chain'][0].query_type,
                'query_complexity': kwargs['access_chain'][0].query_complexity,
                'cache_hit': kwargs['access_chain'][0].hit  # Redis hit
            },
            metadata={
                'access_chain_length': len(kwargs['access_chain']),
                'cache_effectiveness': self.calculate_cache_effectiveness()
            },
            user_id=kwargs.get('user_id')
        )
        
        await self.event_streamer.stream_event(event)
    
    def calculate_cache_effectiveness(self) -> float:
        """Calculate overall cache effectiveness (0-1)"""
        if not self.cache_chains:
            return 0.0
        
        # Cache effectiveness = % of requests served by Redis
        redis_hits = sum(1 for chain in self.cache_chains[-100:] if chain[0].hit)
        total = min(len(self.cache_chains), 100)
        
        return redis_hits / total if total > 0 else 0.0
    
    def get_tier_statistics(self) -> Dict[str, Any]:
        """Get current tier performance statistics"""
        stats = {}
        
        for tier, tier_stats in self.tier_stats.items():
            stats[tier.value] = {
                'hit_rate': tier_stats.hit_rate,
                'avg_latency_ms': tier_stats.avg_latency_ms,
                'p95_latency_ms': tier_stats.p95_latency_ms,
                'p99_latency_ms': tier_stats.p99_latency_ms,
                'total_accesses': tier_stats.total_accesses,
                'items_served': tier_stats.items_served
            }
        
        # Add current hour stats
        stats['current_hour'] = {
            'total_accesses': self.current_hour_stats['accesses'],
            'cache_hit_rate': self.current_hour_stats['cache_hits'] / max(1, self.current_hour_stats['accesses']),
            'avg_latency_ms': self.current_hour_stats['total_latency'] / max(1, self.current_hour_stats['accesses']),
            'estimated_cost': sum(self.current_hour_stats['tier_costs'].values())
        }
        
        return stats
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get optimization suggestions based on access patterns"""
        # Sort by potential savings
        suggestions = sorted(
            self.optimization_candidates[-10:],  # Last 10 suggestions
            key=lambda x: x['potential_savings_ms'] * x['frequency'],
            reverse=True
        )
        
        return suggestions[:5]  # Top 5 suggestions
    
    def get_query_patterns(self) -> Dict[str, Any]:
        """Get query pattern analysis"""
        patterns = []
        
        for pattern_key, data in list(self.query_patterns.items())[:20]:  # Top 20 patterns
            patterns.append({
                'pattern': pattern_key,
                'count': data['count'],
                'avg_latency_ms': data['avg_latency'],
                'tier_distribution': dict(data['tier_distribution'])
            })
        
        # Sort by frequency
        patterns.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'top_patterns': patterns[:10],
            'total_unique_patterns': len(self.query_patterns)
        }
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get cost analysis for memory tier usage"""
        total_cost = sum(self.current_hour_stats['tier_costs'].values())
        
        cost_breakdown = {}
        for tier, cost in self.current_hour_stats['tier_costs'].items():
            cost_breakdown[tier.value] = {
                'cost': cost,
                'percentage': (cost / total_cost * 100) if total_cost > 0 else 0
            }
        
        # Project daily cost
        hours_elapsed = max(1, self.current_hour_stats['accesses'] / 1000)  # Rough estimate
        projected_daily_cost = total_cost * (24 / hours_elapsed)
        
        return {
            'current_cost': total_cost,
            'cost_breakdown': cost_breakdown,
            'projected_daily_cost': projected_daily_cost,
            'cost_per_request': total_cost / max(1, self.current_hour_stats['accesses'])
        }


class TieredMemoryBackend:
    """
    Enhanced memory backend with tier tracking integration
    This wraps existing memory implementations with tracking
    """
    
    def __init__(self,
                 redis_client=None,
                 postgresql_client=None,
                 chromadb_client=None,
                 tier_tracker: Optional[MemoryTierTracker] = None):
        self.redis_client = redis_client
        self.postgresql_client = postgresql_client
        self.chromadb_client = chromadb_client
        self.tier_tracker = tier_tracker
    
    async def retrieve_memories(self,
                               query: str,
                               user_id: Optional[str] = None,
                               agent_id: Optional[str] = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve memories with automatic tier tracking
        """
        
        if self.tier_tracker:
            # Use tracker for monitored access
            result, metrics = await self.tier_tracker.track_memory_access(
                query=query,
                user_id=user_id,
                agent_id=agent_id
            )
            
            logger.info(f"Memory access completed: {metrics['tier_accessed']} "
                       f"(latency: {metrics['total_latency_ms']:.1f}ms)")
            
            return result if result else []
        else:
            # Fallback to direct access without tracking
            # Try tiers in order
            result = await self._try_redis(query, user_id, limit)
            if result:
                return result
            
            result = await self._try_postgresql(query, user_id, limit)
            if result:
                return result
            
            return await self._try_chromadb(query, user_id, limit)
    
    async def _try_redis(self, query: str, user_id: Optional[str], limit: int) -> Optional[List[Dict]]:
        """Direct Redis access"""
        if not self.redis_client:
            return None
        
        try:
            # Implement actual Redis query logic here
            key = f"memory:{user_id}:{query}" if user_id else f"memory:{query}"
            result = await self.redis_client.get(key)
            if result:
                return json.loads(result)[:limit]
        except Exception as e:
            logger.error(f"Redis access error: {e}")
        
        return None
    
    async def _try_postgresql(self, query: str, user_id: Optional[str], limit: int) -> Optional[List[Dict]]:
        """Direct PostgreSQL access"""
        if not self.postgresql_client:
            return None
        
        try:
            # Implement actual PostgreSQL query logic here
            sql = """
                SELECT content, metadata 
                FROM memories 
                WHERE user_id = $1 AND search_vector @@ plainto_tsquery($2)
                LIMIT $3
            """
            rows = await self.postgresql_client.fetch(sql, user_id, query, limit)
            if rows:
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"PostgreSQL access error: {e}")
        
        return None
    
    async def _try_chromadb(self, query: str, user_id: Optional[str], limit: int) -> Optional[List[Dict]]:
        """Direct ChromaDB access"""
        if not self.chromadb_client:
            return []
        
        try:
            # Implement actual ChromaDB query logic here
            collection = self.chromadb_client.get_collection("memories")
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                where={"user_id": user_id} if user_id else None
            )
            
            if results and results['documents']:
                return [
                    {
                        "content": doc,
                        "metadata": meta,
                        "distance": dist
                    }
                    for doc, meta, dist in zip(
                        results['documents'][0],
                        results['metadatas'][0],
                        results['distances'][0]
                    )
                ]
        except Exception as e:
            logger.error(f"ChromaDB access error: {e}")
        
        return [] 