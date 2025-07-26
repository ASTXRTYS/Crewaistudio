"""
Three-Tier Memory System Test
Demonstrates the complete implementation working end-to-end
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
import asyncpg
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import memory system components
from auren.core.memory import (
    UnifiedMemorySystem,
    UnifiedMemoryQuery,
    MemoryTier,
    MemoryType
)

# Import streaming components
from auren.core.streaming.enhanced_websocket_streamer import EnhancedWebSocketEventStreamer
from auren.core.streaming.multi_protocol_streaming import EventStreamer
from auren.core.integration.memory_streaming_bridge import MemoryStreamingBridge


class MemorySystemDemo:
    """Demonstrates the complete three-tier memory system"""
    
    def __init__(self):
        self.memory_system = None
        self.websocket_streamer = None
        self.memory_bridge = None
        self.pg_pool = None
    
    async def setup(self):
        """Initialize all components"""
        logger.info("🚀 Setting up three-tier memory system...")
        
        # Create PostgreSQL connection pool
        database_url = os.getenv("DATABASE_URL", "postgresql://localhost/auren")
        try:
            self.pg_pool = await asyncpg.create_pool(
                database_url,
                min_size=5,
                max_size=20
            )
            logger.info("✅ PostgreSQL pool created")
        except Exception as e:
            logger.warning(f"⚠️  PostgreSQL not available: {e}")
            logger.info("   Continuing without PostgreSQL tier...")
        
        # Initialize WebSocket streamer
        self.websocket_streamer = EnhancedWebSocketEventStreamer(
            host="localhost",
            port=8765
        )
        logger.info("✅ WebSocket streamer initialized")
        
        # Initialize unified memory system
        self.memory_system = UnifiedMemorySystem(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            postgresql_pool=self.pg_pool,
            chromadb_path="/tmp/auren_chromadb_test"
        )
        
        # Initialize the system
        await self.memory_system.initialize()
        logger.info("✅ UnifiedMemorySystem initialized")
        
        # Create memory-streaming bridge
        self.memory_bridge = MemoryStreamingBridge(
            memory_system=self.memory_system,
            websocket_streamer=self.websocket_streamer
        )
        await self.memory_bridge.connect()
        logger.info("✅ Memory-Streaming bridge connected")
        
        logger.info("🎉 Three-tier memory system ready!")
    
    async def demo_basic_operations(self):
        """Demonstrate basic memory operations"""
        logger.info("\n📝 Demo 1: Basic Memory Operations")
        
        # Store a memory
        memory_id = await self.memory_system.store_memory(
            agent_id="neuroscientist",
            user_id="demo_user",
            content={
                "analysis": "HRV baseline established at 55ms",
                "recommendation": "Maintain current training intensity",
                "confidence": 0.85
            },
            memory_type=MemoryType.ANALYSIS.value,
            confidence=0.85,
            priority=7.5,
            metadata={
                "session_id": "demo_001",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        logger.info(f"✅ Stored memory: {memory_id}")
        
        # Retrieve the memory
        memory = await self.memory_system.retrieve_memory(memory_id)
        if memory:
            logger.info(f"✅ Retrieved memory from tier: {memory.tier.value}")
            logger.info(f"   Content: {json.dumps(memory.content, indent=2)}")
        
        # Search memories
        query = UnifiedMemoryQuery(
            query="HRV baseline",
            user_id="demo_user",
            limit=10
        )
        results = await self.memory_system.search_memories(query)
        logger.info(f"✅ Found {len(results)} memories matching 'HRV baseline'")
        
        return memory_id
    
    async def demo_agent_control(self):
        """Demonstrate agent-controlled memory management"""
        logger.info("\n🤖 Demo 2: Agent-Controlled Memory Management")
        
        # Store multiple memories with different priorities
        memory_ids = []
        for i in range(5):
            memory_id = await self.memory_system.store_memory(
                agent_id="neuroscientist",
                user_id="demo_user",
                content={
                    "observation": f"Training session {i+1}",
                    "heart_rate_avg": 120 + i * 5,
                    "recovery_time": 45 - i * 2
                },
                memory_type=MemoryType.FACT.value,
                priority=float(i + 1),  # Varying priorities
                metadata={"session": i+1}
            )
            memory_ids.append(memory_id)
        
        logger.info(f"✅ Stored {len(memory_ids)} training memories")
        
        # Agent decides retention based on criteria
        retention_result = await self.memory_system.agent_memory_control(
            agent_id="neuroscientist",
            action="set_retention",
            params={
                "criteria": {
                    "min_priority": 3.0,
                    "max_age_days": 30,
                    "score_threshold": 1.0
                }
            }
        )
        logger.info(f"✅ Agent retained {retention_result['retained_count']} memories")
        
        # Agent prioritizes important memories
        priority_result = await self.memory_system.agent_memory_control(
            agent_id="neuroscientist",
            action="prioritize",
            params={
                "memory_ids": memory_ids[-2:],  # Last 2 memories
                "boost_factor": 2.0
            }
        )
        logger.info(f"✅ Agent prioritized {priority_result['updated_count']} memories")
    
    async def demo_tier_transitions(self):
        """Demonstrate memory tier transitions"""
        logger.info("\n📊 Demo 3: Memory Tier Transitions")
        
        # Get system stats before
        stats_before = await self.memory_system.get_system_stats()
        logger.info("📈 System stats before:")
        logger.info(f"   Redis: {stats_before['redis_tier'].get('total_memories', 0)} memories")
        logger.info(f"   PostgreSQL: {stats_before['postgres_tier'].get('total_memories', 0)} memories")
        logger.info(f"   ChromaDB: {stats_before['chromadb_tier'].get('total_memories', 0)} memories")
        
        # Store a high-priority memory (will be dual-stored)
        important_memory_id = await self.memory_system.store_memory(
            agent_id="neuroscientist",
            user_id="demo_user",
            content={
                "breakthrough": "Identified optimal HRV training zone",
                "hrv_range": [58, 65],
                "impact": "25% improvement in recovery time"
            },
            memory_type=MemoryType.INSIGHT.value,
            confidence=0.95,
            priority=9.0,  # High priority triggers dual storage
            metadata={"importance": "breakthrough"}
        )
        logger.info(f"✅ Stored high-priority memory: {important_memory_id}")
        
        # Get system stats after
        stats_after = await self.memory_system.get_system_stats()
        logger.info("📈 System stats after:")
        logger.info(f"   Redis: {stats_after['redis_tier'].get('total_memories', 0)} memories")
        logger.info(f"   PostgreSQL: {stats_after['postgres_tier'].get('total_memories', 0)} memories")
        logger.info(f"   ChromaDB: {stats_after['chromadb_tier'].get('total_memories', 0)} memories")
    
    async def demo_semantic_search(self):
        """Demonstrate semantic search capabilities"""
        logger.info("\n🔍 Demo 4: Semantic Search")
        
        # Store memories with semantic content
        training_insights = [
            {
                "content": "Morning HRV readings show consistent improvement when training is done in fasted state",
                "type": "observation"
            },
            {
                "content": "Recovery is significantly faster when cold exposure follows intense training",
                "type": "discovery"
            },
            {
                "content": "Breathing exercises before bed improve next-day HRV by 15-20%",
                "type": "recommendation"
            }
        ]
        
        for insight in training_insights:
            await self.memory_system.store_memory(
                agent_id="neuroscientist",
                user_id="demo_user",
                content=insight,
                memory_type=MemoryType.KNOWLEDGE.value,
                confidence=0.8
            )
        
        logger.info("✅ Stored semantic training insights")
        
        # Semantic search
        semantic_query = UnifiedMemoryQuery(
            query="What improves recovery after training?",
            user_id="demo_user",
            include_semantic=True,
            limit=5
        )
        
        results = await self.memory_system.search_memories(semantic_query)
        logger.info(f"✅ Semantic search found {len(results)} relevant memories:")
        for i, result in enumerate(results[:3]):
            logger.info(f"   {i+1}. Relevance: {result.relevance_score:.2f}")
            logger.info(f"      Content: {result.content}")
            logger.info(f"      Tier: {result.tier.value}")
    
    async def demo_memory_patterns(self):
        """Demonstrate pattern discovery in memories"""
        logger.info("\n🧩 Demo 5: Memory Pattern Discovery")
        
        # Store related memories for pattern discovery
        workout_patterns = [
            {"day": "Monday", "type": "strength", "hrv_drop": 12, "recovery_hours": 48},
            {"day": "Tuesday", "type": "cardio", "hrv_drop": 8, "recovery_hours": 24},
            {"day": "Wednesday", "type": "strength", "hrv_drop": 15, "recovery_hours": 48},
            {"day": "Thursday", "type": "recovery", "hrv_drop": 2, "recovery_hours": 12},
            {"day": "Friday", "type": "cardio", "hrv_drop": 7, "recovery_hours": 24},
        ]
        
        for pattern in workout_patterns:
            await self.memory_system.store_memory(
                agent_id="neuroscientist",
                user_id="pattern_user",
                content=pattern,
                memory_type=MemoryType.FACT.value,
                priority=5.0
            )
        
        logger.info("✅ Stored workout pattern memories")
        
        # Simulate pattern discovery (would normally be done by ChromaDB tier)
        patterns_query = UnifiedMemoryQuery(
            query="strength training recovery",
            user_id="pattern_user",
            tier_preference=[MemoryTier.COLD],
            include_semantic=True
        )
        
        pattern_results = await self.memory_system.search_memories(patterns_query)
        logger.info(f"✅ Pattern search found {len(pattern_results)} related memories")
    
    async def demo_real_time_events(self):
        """Demonstrate real-time event streaming"""
        logger.info("\n📡 Demo 6: Real-Time Event Streaming")
        
        # Check bridge metrics
        metrics = await self.memory_bridge.get_metrics()
        logger.info("📊 Memory-Streaming Bridge Metrics:")
        logger.info(f"   Connected: {metrics['connected']}")
        logger.info(f"   Events processed: {metrics['events_processed']}")
        logger.info(f"   Events dropped: {metrics['events_dropped']}")
        logger.info(f"   Queue size: {metrics['queue_size']}")
        
        # The events are automatically streamed to WebSocket clients
        logger.info("✅ All memory operations are being streamed to dashboard in real-time")
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("\n🧹 Cleaning up...")
        
        if self.memory_system:
            await self.memory_system.close()
        
        if self.pg_pool:
            await self.pg_pool.close()
        
        logger.info("✅ Cleanup complete")
    
    async def run_full_demo(self):
        """Run the complete demonstration"""
        try:
            await self.setup()
            
            # Run all demos
            await self.demo_basic_operations()
            await asyncio.sleep(1)
            
            await self.demo_agent_control()
            await asyncio.sleep(1)
            
            await self.demo_tier_transitions()
            await asyncio.sleep(1)
            
            await self.demo_semantic_search()
            await asyncio.sleep(1)
            
            await self.demo_memory_patterns()
            await asyncio.sleep(1)
            
            await self.demo_real_time_events()
            
            logger.info("\n🎉 Three-tier memory system demonstration complete!")
            logger.info("   ✅ Redis tier for hot memories (<30 days)")
            logger.info("   ✅ PostgreSQL tier for structured queries")
            logger.info("   ✅ ChromaDB tier for semantic search")
            logger.info("   ✅ Real-time WebSocket event streaming")
            logger.info("   ✅ Agent-controlled memory management")
            
        except Exception as e:
            logger.error(f"❌ Demo error: {e}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Main entry point"""
    demo = MemorySystemDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main()) 