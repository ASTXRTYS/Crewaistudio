"""
Memory Tier Integration - Adding tier tracking to Module D agents
Shows how memory access patterns are tracked across Redis, PostgreSQL, and ChromaDB
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging

# Import memory tier tracking
from auren.realtime.memory_tier_tracking import MemoryTierTracker, TieredMemoryBackend, MemoryTier

# Import from Module C
from auren.realtime.crewai_instrumentation import CrewAIEventInstrumentation, AURENEventType
from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer

# Import from Module D
from auren.agents.memory import AURENMemory, AURENMemoryStorage

logger = logging.getLogger(__name__)


class TieredAURENMemoryStorage(AURENMemoryStorage):
    """
    Enhanced AUREN memory storage with tier tracking
    This replaces the standard memory storage with tier-aware version
    """
    
    def __init__(self, 
                 memory_backend,
                 event_store,
                 hypothesis_validator,
                 knowledge_manager,
                 agent_id: str,
                 user_id: Optional[str] = None,
                 tier_tracker: Optional[MemoryTierTracker] = None):
        
        super().__init__(
            memory_backend, event_store, hypothesis_validator,
            knowledge_manager, agent_id, user_id
        )
        
        # Create tiered backend wrapper
        self.tiered_backend = TieredMemoryBackend(
            redis_client=getattr(memory_backend, 'redis_client', None),
            postgresql_client=getattr(memory_backend, 'postgresql_client', None),
            chromadb_client=getattr(memory_backend, 'chromadb_client', None),
            tier_tracker=tier_tracker
        )
        
        self.tier_tracker = tier_tracker
    
    async def load(self, query: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """Load memories with tier tracking"""
        
        try:
            # Use tiered backend for tracked access
            memories = await self.tiered_backend.retrieve_memories(
                query=query,
                user_id=self.user_id,
                agent_id=self.agent_id,
                limit=limit
            )
            
            # Also perform standard CrewAI operations
            crew_memories = []
            for memory in memories:
                crew_memory = self._convert_to_crew_format(memory)
                if self._matches_query(crew_memory, query):
                    crew_memories.append(crew_memory)
            
            return crew_memories[:limit]
            
        except Exception as e:
            logger.error(f"Error loading memories with tier tracking: {e}")
            # Fallback to standard load
            return await super().load(query, limit)


async def setup_memory_tier_monitoring(config: Dict[str, Any]):
    """
    Setup memory tier tracking for AUREN system
    Integrates with existing Module C & D components
    """
    
    # 1. Initialize event streaming (for tier access events)
    redis_streamer = RedisStreamEventStreamer(
        redis_url=config["redis_url"],
        stream_name="auren:events"
    )
    await redis_streamer.initialize()
    
    # 2. Create memory tier tracker
    tier_tracker = MemoryTierTracker(
        event_streamer=redis_streamer,
        metrics_window_size=1000,  # Keep last 1000 accesses
        stats_update_interval=60   # Update stats every minute
    )
    
    logger.info("Memory tier tracking initialized")
    
    # 3. Create event instrumentation
    event_instrumentation = CrewAIEventInstrumentation(
        event_streamer=redis_streamer
    )
    
    # 4. Enhance all Module D agents with tiered memory
    # This would be done in the orchestrator initialization
    
    return {
        "tier_tracker": tier_tracker,
        "event_instrumentation": event_instrumentation,
        "redis_streamer": redis_streamer
    }


def enhance_agent_with_tier_tracking(agent_wrapper, tier_tracker: MemoryTierTracker):
    """
    Enhance a Module D agent with memory tier tracking
    """
    
    if hasattr(agent_wrapper, 'memory') and isinstance(agent_wrapper.memory, AURENMemory):
        # Get existing memory configuration
        old_storage = agent_wrapper.memory.storage
        
        # Create new tiered storage
        tiered_storage = TieredAURENMemoryStorage(
            memory_backend=old_storage.memory_backend,
            event_store=old_storage.event_store,
            hypothesis_validator=old_storage.hypothesis_validator,
            knowledge_manager=old_storage.knowledge_manager,
            agent_id=old_storage.agent_id,
            user_id=old_storage.user_id,
            tier_tracker=tier_tracker
        )
        
        # Replace storage
        agent_wrapper.memory.storage = tiered_storage
        
        logger.info(f"Enhanced {old_storage.agent_id} with memory tier tracking")


async def demonstrate_memory_tier_tracking():
    """Demonstrate memory tier tracking in action"""
    
    config = {
        "redis_url": "redis://localhost:6379",
        # ... other config
    }
    
    # Setup tier tracking
    monitoring = await setup_memory_tier_monitoring(config)
    tier_tracker = monitoring["tier_tracker"]
    
    # Simulate various memory access patterns
    print("\n=== Memory Tier Tracking Demo ===")
    
    # 1. Frequently accessed query (should be in Redis)
    print("\n1. Accessing frequently used data...")
    result1, metrics1 = await tier_tracker.track_memory_access(
        query="What is my average HRV?",
        user_id="demo_user",
        agent_id="neuroscientist"
    )
    print(f"   Tier: {metrics1['tier_accessed']}")
    print(f"   Latency: {metrics1['total_latency_ms']:.1f}ms")
    print(f"   Cache hit: {metrics1['access_chain'][0]['hit']}")
    
    # 2. Less common query (might be in PostgreSQL)
    print("\n2. Accessing structured historical data...")
    result2, metrics2 = await tier_tracker.track_memory_access(
        query="Show my workout history from last month",
        user_id="demo_user",
        agent_id="training_agent"
    )
    print(f"   Tier: {metrics2['tier_accessed']}")
    print(f"   Latency: {metrics2['total_latency_ms']:.1f}ms")
    
    # 3. Complex semantic query (likely ChromaDB)
    print("\n3. Semantic search query...")
    result3, metrics3 = await tier_tracker.track_memory_access(
        query="Find patterns between my sleep quality and workout performance",
        user_id="demo_user",
        agent_id="neuroscientist"
    )
    print(f"   Tier: {metrics3['tier_accessed']}")
    print(f"   Latency: {metrics3['total_latency_ms']:.1f}ms")
    
    # Get statistics
    stats = tier_tracker.get_tier_statistics()
    print("\n=== Tier Performance Statistics ===")
    for tier_name, tier_stats in stats.items():
        if tier_name != 'current_hour':
            print(f"\n{tier_name.upper()}:")
            print(f"  Hit rate: {tier_stats.get('hit_rate', 0):.1%}")
            print(f"  Avg latency: {tier_stats.get('avg_latency_ms', 0):.1f}ms")
            print(f"  P95 latency: {tier_stats.get('p95_latency_ms', 0):.1f}ms")
    
    # Cache effectiveness
    effectiveness = tier_tracker.calculate_cache_effectiveness()
    print(f"\n=== Cache Effectiveness: {effectiveness:.1%} ===")
    
    # Cost analysis
    cost_analysis = tier_tracker.get_cost_analysis()
    print(f"\n=== Cost Analysis ===")
    print(f"Current cost: ${cost_analysis['current_cost']:.4f}")
    print(f"Projected daily: ${cost_analysis['projected_daily_cost']:.2f}")
    
    # Optimization suggestions
    suggestions = tier_tracker.get_optimization_suggestions()
    if suggestions:
        print(f"\n=== Optimization Suggestions ===")
        for suggestion in suggestions[:3]:
            print(f"- {suggestion['suggestion']}")
            print(f"  Pattern: '{suggestion['pattern']}'")
            print(f"  Potential savings: {suggestion['potential_savings_ms']:.0f}ms per query")


def verify_tier_tracking_implementation():
    """Verification checklist for memory tier tracking"""
    
    checklist = {
        "Redis Tracking": {
            "requirement": "Track Redis cache hits/misses",
            "test": "Run query multiple times - should hit Redis on repeat",
            "dashboard": "Shows Redis hit rate percentage"
        },
        "PostgreSQL Fallback": {
            "requirement": "Track PostgreSQL access when Redis misses",
            "test": "Query unique data - should fall through to PostgreSQL",
            "dashboard": "Shows PostgreSQL access frequency"
        },
        "ChromaDB Semantic": {
            "requirement": "Track ChromaDB for semantic searches",
            "test": "Complex semantic query - should reach ChromaDB",
            "dashboard": "Shows ChromaDB usage and latency"
        },
        "Latency Measurements": {
            "requirement": "Accurate latency for each tier",
            "test": "Compare tier latencies - Redis < PostgreSQL < ChromaDB",
            "dashboard": "Bar chart showing latency comparison"
        },
        "Cache Effectiveness": {
            "requirement": "Calculate overall cache hit rate",
            "test": "Run mixed queries - check effectiveness %",
            "dashboard": "Shows cache effectiveness gauge"
        },
        "Cost Tracking": {
            "requirement": "Track access costs per tier",
            "test": "Monitor cost accumulation",
            "dashboard": "Shows cost breakdown by tier"
        }
    }
    
    print("\n=== Memory Tier Tracking Checklist ===")
    for feature, details in checklist.items():
        print(f"\n{feature}:")
        print(f"  ✓ Requirement: {details['requirement']}")
        print(f"  ✓ Test: {details['test']}")
        print(f"  ✓ Dashboard: {details['dashboard']}")
    
    return checklist


# Example of how to integrate with Module D orchestrator
class MemoryTierAwareOrchestrator:
    """Example orchestrator with memory tier tracking"""
    
    def __init__(self, tier_tracker: MemoryTierTracker, *args, **kwargs):
        # Standard orchestrator init
        super().__init__(*args, **kwargs)
        self.tier_tracker = tier_tracker
        
        # Enhance all agents with tier tracking
        for agent_id, agent_wrapper in self.agents.items():
            enhance_agent_with_tier_tracking(agent_wrapper, tier_tracker)
    
    async def get_memory_tier_metrics(self) -> Dict[str, Any]:
        """Get current memory tier metrics for dashboard"""
        
        return {
            "tier_statistics": self.tier_tracker.get_tier_statistics(),
            "cache_effectiveness": self.tier_tracker.calculate_cache_effectiveness(),
            "query_patterns": self.tier_tracker.get_query_patterns(),
            "cost_analysis": self.tier_tracker.get_cost_analysis(),
            "optimization_suggestions": self.tier_tracker.get_optimization_suggestions()
        }


if __name__ == "__main__":
    # Run verification
    verify_tier_tracking_implementation()
    
    # Run demonstration
    asyncio.run(demonstrate_memory_tier_tracking()) 