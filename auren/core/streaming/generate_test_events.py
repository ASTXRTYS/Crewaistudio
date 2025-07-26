"""
Generate test events to demonstrate the real-time event pipeline
"""

import asyncio
import random
from datetime import datetime, timezone
from auren.realtime.crewai_instrumentation import (
    CrewAIEventInstrumentation, 
    AURENStreamEvent, 
    AURENEventType,
    AURENPerformanceMetrics
)
from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_test_events():
    """Generate various test events to demonstrate the pipeline"""
    
    # Initialize Redis Streamer
    redis_streamer = RedisStreamEventStreamer(
        redis_url="redis://localhost:6379",
        stream_name="auren:events"
    )
    await redis_streamer.initialize()
    logger.info("✅ Redis streamer initialized")
    
    # Initialize instrumentation
    instrumentation = CrewAIEventInstrumentation(
        event_streamer=redis_streamer
    )
    logger.info("✅ Event instrumentation initialized")
    
    # Agent names for variety
    agents = ["neuroscientist", "nutritionist", "training_coach", "recovery_agent", "sleep_specialist"]
    models = ["gpt-4", "gpt-3.5-turbo", "claude-2"]
    
    event_count = 0
    
    while True:
        try:
            # Generate different types of events randomly
            event_type = random.choice([
                "agent_start", "agent_complete", "llm_call", 
                "collaboration", "decision", "memory_tier"
            ])
            
            if event_type == "agent_start":
                agent = random.choice(agents)
                event = AURENStreamEvent(
                    event_id=f"demo_{event_count:04d}",
                    trace_id=f"trace_{event_count // 10}",
                    session_id=f"session_{event_count // 20}",
                    timestamp=datetime.now(timezone.utc),
                    event_type=AURENEventType.AGENT_EXECUTION_STARTED,
                    source_agent={
                        "id": agent,
                        "role": agent.replace("_", " ").title(),
                        "goal": f"Optimize {agent.split('_')[0]} performance"
                    },
                    target_agent=None,
                    payload={
                        "execution_mode": "autonomous",
                        "tools_available": random.randint(2, 5)
                    },
                    metadata={
                        "test": True,
                        "demo_event": True
                    }
                )
                
            elif event_type == "agent_complete":
                agent = random.choice(agents)
                latency = random.randint(500, 3000)
                event = AURENStreamEvent(
                    event_id=f"demo_{event_count:04d}",
                    trace_id=f"trace_{event_count // 10}",
                    session_id=f"session_{event_count // 20}",
                    timestamp=datetime.now(timezone.utc),
                    event_type=AURENEventType.AGENT_EXECUTION_COMPLETED,
                    source_agent={
                        "id": agent,
                        "role": agent.replace("_", " ").title()
                    },
                    target_agent=None,
                    payload={
                        "execution_result": "success" if random.random() > 0.1 else "error",
                        "output_length": random.randint(100, 1000)
                    },
                    metadata={
                        "session_duration_ms": latency
                    },
                    performance_metrics=AURENPerformanceMetrics(
                        latency_ms=latency,
                        token_cost=random.uniform(0.01, 0.10),
                        memory_usage_mb=random.uniform(100, 200),
                        cpu_percentage=random.uniform(10, 50),
                        success=random.random() > 0.1,
                        agent_id=agent,
                        confidence_score=random.uniform(0.7, 0.95)
                    )
                )
                
            elif event_type == "llm_call":
                agent = random.choice(agents)
                model = random.choice(models)
                tokens = random.randint(100, 2000)
                event = AURENStreamEvent(
                    event_id=f"demo_{event_count:04d}",
                    trace_id=f"trace_{event_count // 10}",
                    session_id=f"session_{event_count // 20}",
                    timestamp=datetime.now(timezone.utc),
                    event_type=AURENEventType.LLM_CALL,
                    source_agent={
                        "id": agent,
                        "role": agent.replace("_", " ").title()
                    },
                    target_agent=None,
                    payload={
                        "model": model,
                        "tokens_used": tokens,
                        "cost": tokens * 0.00002,  # Rough cost estimate
                        "success": True,
                        "latency_ms": random.randint(200, 2000)
                    },
                    metadata={
                        "provider": "openai" if "gpt" in model else "anthropic"
                    }
                )
                
            elif event_type == "collaboration":
                primary = random.choice(agents)
                collaborators = random.sample([a for a in agents if a != primary], k=random.randint(1, 3))
                event = AURENStreamEvent(
                    event_id=f"demo_{event_count:04d}",
                    trace_id=f"trace_collab_{event_count}",
                    session_id=f"collab_session_{event_count}",
                    timestamp=datetime.now(timezone.utc),
                    event_type=AURENEventType.AGENT_COLLABORATION,
                    source_agent={
                        "id": primary,
                        "role": primary.replace("_", " ").title()
                    },
                    target_agent=None,
                    payload={
                        "primary_agent": primary,
                        "collaborating_agents": collaborators,
                        "collaboration_type": "health_optimization",
                        "consensus_reached": random.random() > 0.2,
                        "confidence_scores": {
                            agent: random.uniform(0.7, 0.95) 
                            for agent in [primary] + collaborators
                        },
                        "resolution_time_ms": random.randint(5000, 30000),
                        "knowledge_shared": random.randint(1, 5)
                    },
                    metadata={
                        "domains_involved": [a.split("_")[0] for a in [primary] + collaborators]
                    }
                )
                
            elif event_type == "decision":
                agent = random.choice(agents)
                event = AURENStreamEvent(
                    event_id=f"demo_{event_count:04d}",
                    trace_id=f"trace_decision_{event_count}",
                    session_id=f"decision_session_{event_count}",
                    timestamp=datetime.now(timezone.utc),
                    event_type=AURENEventType.AGENT_DECISION,
                    source_agent={
                        "id": agent,
                        "role": agent.replace("_", " ").title()
                    },
                    target_agent=None,
                    payload={
                        "decision": {
                            "type": "recommendation",
                            "action": f"Optimize {agent.split('_')[0]} protocol",
                            "category": "health_optimization"
                        },
                        "confidence": random.uniform(0.7, 0.95),
                        "reasoning_chain": ["Analyzed data", "Compared patterns", "Generated recommendation"],
                        "data_sources": ["biometric_data", "historical_patterns", "research_papers"],
                        "decision_impact": "high"
                    },
                    metadata={
                        "decision_category": "optimization",
                        "urgency": random.choice(["low", "normal", "high"])
                    },
                    user_id="test_user_001"
                )
                
            elif event_type == "memory_tier":
                tier = random.choice(["redis_immediate", "postgresql_structured", "chromadb_semantic"])
                latency = {"redis_immediate": 5, "postgresql_structured": 25, "chromadb_semantic": 150}[tier]
                event = AURENStreamEvent(
                    event_id=f"demo_{event_count:04d}",
                    trace_id=f"trace_memory_{event_count}",
                    session_id=f"memory_session_{event_count}",
                    timestamp=datetime.now(timezone.utc),
                    event_type=AURENEventType.MEMORY_TIER_ACCESS,
                    source_agent={
                        "id": random.choice(agents),
                        "role": "Memory System"
                    },
                    target_agent=None,
                    payload={
                        "tier_accessed": tier,
                        "query": "Recent health patterns",
                        "latency_by_tier": {
                            "redis": latency if tier == "redis_immediate" else 0,
                            "postgresql": latency if tier == "postgresql_structured" else 0,
                            "chromadb": latency if tier == "chromadb_semantic" else 0
                        },
                        "items_retrieved": random.randint(1, 20)
                    },
                    metadata={
                        "cache_hit": tier == "redis_immediate",
                        "memory_type": "episodic"
                    }
                )
            
            # Send the event
            success = await redis_streamer.stream_event(event)
            if success:
                logger.info(f"✅ Sent {event_type} event #{event_count:04d}")
            else:
                logger.error(f"❌ Failed to send event #{event_count:04d}")
            
            event_count += 1
            
            # Wait a bit before next event (adjust for desired rate)
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
        except Exception as e:
            logger.error(f"Error generating event: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    logger.info("=== Starting Test Event Generator ===")
    logger.info("Press Ctrl+C to stop")
    
    try:
        asyncio.run(generate_test_events())
    except KeyboardInterrupt:
        logger.info("\n✅ Event generator stopped") 