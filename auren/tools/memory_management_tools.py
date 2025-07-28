"""
Memory Management Tools for NEUROS
Created: July 28, 2025
Purpose: Enable NEUROS to actively manage the three-tier memory system
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import redis
import asyncpg
from chromadb import Client as ChromaClient
import json
from dataclasses import dataclass
from enum import Enum


class MemoryTier(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


@dataclass
class Memory:
    id: str
    content: Any
    tier: MemoryTier
    created_at: datetime
    last_accessed: datetime
    access_count: int
    relevance_score: float
    metadata: Dict[str, Any]


class MemoryManagementTools:
    """Tools for NEUROS to manage three-tier memory system"""
    
    def __init__(self, redis_client: redis.Redis, pg_pool: asyncpg.Pool, chroma_client: ChromaClient):
        self.redis = redis_client
        self.pg_pool = pg_pool
        self.chroma = chroma_client
        self.hot_tier_ttl = timedelta(days=30)
        
    async def search_all_tiers(
        self, 
        query: str, 
        user_id: str,
        limit: int = 10,
        time_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Unified search across all memory tiers
        Returns relevance-ranked results with tier source
        """
        results = []
        
        # Search hot tier (Redis)
        hot_results = await self._search_hot_tier(query, user_id)
        for result in hot_results:
            result['tier'] = 'hot'
            result['tier_metaphor'] = 'Active Mind'
            results.append(result)
        
        # Search warm tier (PostgreSQL)
        warm_results = await self._search_warm_tier(query, user_id, time_range)
        for result in warm_results:
            result['tier'] = 'warm'
            result['tier_metaphor'] = 'Structured Journal'
            results.append(result)
        
        # Search cold tier (ChromaDB)
        cold_results = await self._search_cold_tier(query, user_id, limit)
        for result in cold_results:
            result['tier'] = 'cold'
            result['tier_metaphor'] = 'Deep Library'
            results.append(result)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return results[:limit]
    
    async def promote_memory(
        self,
        memory_id: str,
        target_tier: MemoryTier,
        duration: Optional[timedelta] = None,
        reason: str = "User requested"
    ) -> Dict[str, Any]:
        """
        Move memory to a higher tier
        Returns success status and explanation
        """
        # Find current location
        current_tier, memory_data = await self._find_memory(memory_id)
        
        if not memory_data:
            return {
                'success': False,
                'explanation': "Memory not found in any tier"
            }
        
        # Determine promotion path
        if current_tier == target_tier:
            return {
                'success': False,
                'explanation': f"Memory already in {target_tier.value} tier"
            }
        
        # Perform promotion
        if target_tier == MemoryTier.HOT:
            await self._promote_to_hot(memory_id, memory_data, duration)
            explanation = f"Promoted to active mind for immediate access. Reason: {reason}"
        elif target_tier == MemoryTier.WARM:
            await self._promote_to_warm(memory_id, memory_data)
            explanation = f"Promoted to structured journal for analysis. Reason: {reason}"
        else:
            return {
                'success': False,
                'explanation': "Cannot promote to cold tier - cold is for archival only"
            }
        
        # Log the promotion
        await self._log_memory_movement(memory_id, current_tier, target_tier, reason)
        
        return {
            'success': True,
            'explanation': explanation,
            'from_tier': current_tier.value,
            'to_tier': target_tier.value,
            'memory_id': memory_id
        }
    
    async def analyze_memory_patterns(
        self,
        user_id: str,
        time_range: tuple,
        pattern_type: str = "all",
        correlation_factors: List[str] = None
    ) -> Dict[str, Any]:
        """
        Find patterns across time periods
        Analyzes correlations between memories and outcomes
        """
        patterns = {
            'recurring_patterns': [],
            'successful_interventions': [],
            'correlation_insights': [],
            'temporal_clusters': []
        }
        
        # Query warm tier for structured analysis
        async with self.pg_pool.acquire() as conn:
            # Find recurring patterns
            if pattern_type in ["all", "recurring"]:
                recurring = await conn.fetch("""
                    SELECT pattern_type, COUNT(*) as occurrences, 
                           AVG(outcome_score) as avg_success
                    FROM memory_patterns
                    WHERE user_id = $1 
                    AND created_at BETWEEN $2 AND $3
                    GROUP BY pattern_type
                    HAVING COUNT(*) >= 3
                    ORDER BY occurrences DESC
                """, user_id, time_range[0], time_range[1])
                patterns['recurring_patterns'] = [dict(r) for r in recurring]
            
            # Find successful interventions
            if pattern_type in ["all", "interventions"]:
                successful = await conn.fetch("""
                    SELECT intervention_type, context, outcome_score
                    FROM memory_patterns
                    WHERE user_id = $1
                    AND created_at BETWEEN $2 AND $3
                    AND outcome_score > 0.8
                    ORDER BY outcome_score DESC
                    LIMIT 10
                """, user_id, time_range[0], time_range[1])
                patterns['successful_interventions'] = [dict(r) for r in successful]
        
        # Add pattern explanations
        patterns['summary'] = self._generate_pattern_summary(patterns)
        
        return patterns
    
    async def explain_memory_decision(
        self,
        decision_type: str,
        memory_id: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable explanation of memory management decision
        """
        explanations = {
            'promotion': [
                "I brought this forward because you're working on a similar challenge",
                "This pattern has proven successful 3 times - keeping it readily accessible",
                "Your current protocol matches this historical success - promoting for easy reference"
            ],
            'demotion': [
                "This memory hasn't been accessed in 25 days - moving to structured storage",
                "Making room in active memory while preserving this insight",
                "Archiving completed protocol while keeping key learnings accessible"
            ],
            'retrieval': [
                "Found this in your {tier} - it matches your current situation",
                "Retrieved from {tier} based on semantic similarity",
                "This historical pattern from {tier} shows strong correlation"
            ]
        }
        
        # Get memory details
        tier, memory_data = await self._find_memory(memory_id)
        
        # Build contextual explanation
        base_explanation = explanations.get(decision_type, ["Memory operation completed"])[0]
        
        if '{tier}' in base_explanation:
            tier_metaphor = {
                MemoryTier.HOT: "active mind",
                MemoryTier.WARM: "structured journal",
                MemoryTier.COLD: "deep library"
            }
            base_explanation = base_explanation.format(tier=tier_metaphor.get(tier, tier.value))
        
        # Add specific context
        if context.get('relevance_score'):
            base_explanation += f" (relevance: {context['relevance_score']:.0%})"
        
        return base_explanation
    
    async def memory_health_check(self, user_id: str) -> Dict[str, Any]:
        """
        Monitor tier usage and optimization opportunities
        Returns statistics and recommendations
        """
        health_report = {
            'tier_usage': {},
            'performance_metrics': {},
            'recommendations': [],
            'optimization_opportunities': []
        }
        
        # Check hot tier (Redis)
        hot_keys = await self._count_hot_memories(user_id)
        hot_memory_usage = await self._calculate_hot_memory_size(user_id)
        health_report['tier_usage']['hot'] = {
            'count': hot_keys,
            'size_mb': hot_memory_usage,
            'capacity_used': f"{(hot_memory_usage / 100) * 100:.1f}%"  # Assuming 100MB limit
        }
        
        # Check warm tier (PostgreSQL)
        async with self.pg_pool.acquire() as conn:
            warm_stats = await conn.fetchrow("""
                SELECT COUNT(*) as count, 
                       SUM(pg_column_size(content)) / 1024 / 1024 as size_mb
                FROM memory_patterns
                WHERE user_id = $1
            """, user_id)
            health_report['tier_usage']['warm'] = {
                'count': warm_stats['count'],
                'size_mb': float(warm_stats['size_mb'] or 0)
            }
        
        # Generate recommendations
        if hot_keys > 100:
            health_report['recommendations'].append(
                "High hot tier usage - consider archiving completed protocols"
            )
        
        if hot_memory_usage > 80:
            health_report['optimization_opportunities'].append({
                'action': 'selective_demotion',
                'reason': 'Hot tier approaching capacity',
                'suggested_candidates': await self._find_demotion_candidates(user_id)
            })
        
        # Add performance metrics
        health_report['performance_metrics'] = {
            'avg_retrieval_time_ms': 45,  # Would be calculated from actual metrics
            'hot_tier_hit_rate': 0.87,
            'pattern_discovery_rate': 'increasing'
        }
        
        return health_report
    
    # Helper methods
    async def _search_hot_tier(self, query: str, user_id: str) -> List[Dict]:
        """Search Redis for recent memories"""
        # Implementation would search Redis keys and values
        return []
    
    async def _search_warm_tier(self, query: str, user_id: str, time_range: Optional[tuple]) -> List[Dict]:
        """Search PostgreSQL for structured memories"""
        # Implementation would use full-text search or pattern matching
        return []
    
    async def _search_cold_tier(self, query: str, user_id: str, limit: int) -> List[Dict]:
        """Search ChromaDB for semantic memories"""
        # Implementation would use ChromaDB's semantic search
        return []
    
    async def _find_memory(self, memory_id: str) -> tuple[MemoryTier, Dict]:
        """Locate a memory across all tiers"""
        # Check each tier and return location and data
        return MemoryTier.WARM, {}
    
    async def _promote_to_hot(self, memory_id: str, data: Dict, duration: Optional[timedelta]):
        """Move memory to Redis with TTL"""
        ttl = duration or self.hot_tier_ttl
        self.redis.setex(
            f"memory:{memory_id}",
            ttl,
            json.dumps(data)
        )
    
    async def _promote_to_warm(self, memory_id: str, data: Dict):
        """Move memory to PostgreSQL"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO memory_patterns (id, user_id, content, created_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE SET last_accessed = NOW()
            """, memory_id, data.get('user_id'), json.dumps(data), datetime.now())
    
    async def _log_memory_movement(self, memory_id: str, from_tier: MemoryTier, to_tier: MemoryTier, reason: str):
        """Log memory tier movements for observability"""
        # Would integrate with Prometheus metrics here
        pass
    
    def _generate_pattern_summary(self, patterns: Dict) -> str:
        """Generate human-readable pattern summary"""
        recurring_count = len(patterns['recurring_patterns'])
        successful_count = len(patterns['successful_interventions'])
        
        return (f"Found {recurring_count} recurring patterns and "
                f"{successful_count} successful interventions in this time period")
    
    async def _count_hot_memories(self, user_id: str) -> int:
        """Count memories in Redis for user"""
        # Implementation would count Redis keys for user
        return 75  # Example
    
    async def _calculate_hot_memory_size(self, user_id: str) -> float:
        """Calculate total size of hot memories in MB"""
        # Implementation would sum Redis memory usage
        return 45.2  # Example
    
    async def _find_demotion_candidates(self, user_id: str) -> List[str]:
        """Find memories suitable for demotion"""
        # Would analyze access patterns and suggest least-used memories
        return ["memory_123", "memory_456"]


# Example usage in NEUROS
async def neuros_memory_example(tools: MemoryManagementTools, user_id: str):
    """Example of how NEUROS would use these tools"""
    
    # When user mentions past success
    results = await tools.search_all_tiers(
        query="morning protocol success",
        user_id=user_id,
        limit=5
    )
    
    # Explain findings
    for result in results:
        print(f"Found in {result['tier_metaphor']}: {result['summary']}")
    
    # Promote relevant memory
    if results and results[0]['tier'] != 'hot':
        promotion_result = await tools.promote_memory(
            memory_id=results[0]['id'],
            target_tier=MemoryTier.HOT,
            duration=timedelta(days=7),
            reason="User starting similar protocol"
        )
        print(f"Memory management: {promotion_result['explanation']}")
    
    # Check memory health
    health = await tools.memory_health_check(user_id)
    if health['recommendations']:
        print(f"Memory optimization needed: {health['recommendations'][0]}") 