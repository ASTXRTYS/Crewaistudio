"""
Test script that sends REAL events through the complete pipeline
This will make the dashboard come alive with actual data!
"""

import asyncio
import random
from datetime import datetime, timezone
from auren.realtime.langgraph_instrumentation import (
    AURENStreamEvent, 
    AURENEventType,
    AURENPerformanceMetrics
)
from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_live_events():
    """Send events through Redis that will appear on the dashboard"""
    
    # Initialize Redis Streamer - this connects to the actual pipeline!
    redis_streamer = RedisStreamEventStreamer(
        redis_url="redis://localhost:6379",
        stream_name="auren:events"  # Same stream the WebSocket server is listening to
    )
    await redis_streamer.initialize()
    
    logger.info("🚀 Starting LIVE event stream to dashboard...")
    
    # ONLY ONE AGENT - The Neuroscientist specializing in CNS optimization
    agent = "neuroscientist"
    agent_details = {
        "id": "neuroscientist",
        "role": "CNS Optimization Specialist",
        "specialty": "Tier-one operator performance",
        "focus": "Central Nervous System fatigue and recovery"
    }
    
    event_count = 0
    
    while True:
        # Generate different event types with realistic distribution
        event_type_choice = random.random()
        
        if event_type_choice < 0.2:  # 20% - Agent starts
            event = AURENStreamEvent(
                event_id=str(uuid.uuid4()),
                trace_id=str(uuid.uuid4()),
                session_id=f"session_{agent}_{datetime.now().timestamp()}",
                timestamp=datetime.now(timezone.utc),
                event_type=AURENEventType.AGENT_EXECUTION_STARTED,
                source_agent=agent_details,
                target_agent=None,
                payload={
                    "goal": "Analyzing CNS fatigue patterns and recovery metrics",
                    "tools_available": ["hrv_analyzer", "neural_fatigue_detector", "recovery_optimizer"],
                    "focus_area": random.choice(["HRV analysis", "sleep quality", "stress response", "recovery patterns"])
                },
                metadata={"platform": "langgraph", "version": "0.2.27"},
                user_id="test_user"
            )
            
        elif event_type_choice < 0.4:  # 20% - LLM calls
            tokens = random.randint(500, 3000)  # Neuroscientist uses more tokens for complex analysis
            cost = tokens * 0.00003  # Rough cost estimate
            
            event = AURENStreamEvent(
                event_id=str(uuid.uuid4()),
                trace_id=str(uuid.uuid4()),
                session_id=f"session_{agent}_{datetime.now().timestamp()}",
                timestamp=datetime.now(timezone.utc),
                event_type=AURENEventType.LLM_CALL,
                source_agent=agent_details,
                target_agent=None,
                payload={
                    "model": "gpt-4",  # Neuroscientist uses GPT-4 for complex CNS analysis
                    "tokens_used": tokens,
                    "cost": cost,
                    "latency_ms": random.randint(800, 2500),
                    "success": True,
                    "purpose": random.choice([
                        "CNS fatigue analysis",
                        "HRV pattern recognition", 
                        "Recovery protocol generation",
                        "Stress response evaluation"
                    ])
                },
                metadata={"complexity": "high"},
                user_id="test_user"
            )
            
        elif event_type_choice < 0.5:  # 10% - Memory tier access
            tier = random.choice(["redis", "postgresql", "chromadb"])
            latencies = {"redis": 5, "postgresql": 25, "chromadb": 150}
            
            event = AURENStreamEvent(
                event_id=str(uuid.uuid4()),
                trace_id=str(uuid.uuid4()),
                session_id=f"memory_{datetime.now().timestamp()}",
                timestamp=datetime.now(timezone.utc),
                event_type=AURENEventType.MEMORY_TIER_ACCESS,
                source_agent=agent_details,
                target_agent=None,
                payload={
                    "tier_accessed": tier,
                    "latency_ms": latencies[tier] + random.randint(-5, 5),
                    "items_retrieved": random.randint(1, 15),
                    "query": random.choice([
                        "user_hrv_baseline",
                        "cns_recovery_patterns",
                        "stress_response_history",
                        "sleep_quality_trends",
                        "fatigue_indicators"
                    ])
                },
                metadata={"cache_hit": random.random() > 0.3},
                user_id="test_user"
            )
            
        elif event_type_choice < 0.55:  # 5% - Hypothesis formation (Neuroscientist specialty)
            event = AURENStreamEvent(
                event_id=str(uuid.uuid4()),
                trace_id=str(uuid.uuid4()),
                session_id=f"hypothesis_{datetime.now().timestamp()}",
                timestamp=datetime.now(timezone.utc),
                event_type=AURENEventType.HYPOTHESIS_FORMATION,
                source_agent=agent_details,
                target_agent=None,
                payload={
                    "hypothesis": random.choice([
                        "User's HRV decline correlates with increased training volume",
                        "Morning recovery scores predict afternoon performance",
                        "Sleep efficiency impacts next-day CNS readiness",
                        "Stress markers indicate need for recovery protocol adjustment"
                    ]),
                    "confidence": random.uniform(0.7, 0.95),
                    "evidence_points": random.randint(3, 8),
                    "validation_timeline": f"{random.randint(3, 14)} days"
                },
                metadata={"domain": "neuroscience"},
                user_id="test_user"
            )
            
        elif event_type_choice < 0.65:  # 10% - Agent decision
            event = AURENStreamEvent(
                event_id=str(uuid.uuid4()),
                trace_id=str(uuid.uuid4()),
                session_id=f"decision_{datetime.now().timestamp()}",
                timestamp=datetime.now(timezone.utc),
                event_type=AURENEventType.AGENT_DECISION,
                source_agent=agent_details,
                target_agent=None,
                payload={
                    "decision": {
                        "type": random.choice(["recommendation", "alert", "insight"]),
                        "content": random.choice([
                            "CNS fatigue detected - recommend 48hr recovery protocol",
                            "HRV patterns indicate optimal training window",
                            "Sleep quality insufficient for tier-one performance",
                            "Stress adaptation positive - increase training load safe"
                        ]),
                        "confidence": random.uniform(0.8, 0.95),
                        "priority": random.choice(["high", "medium", "low"])
                    },
                    "reasoning_steps": random.randint(5, 12),
                    "data_sources": ["HRV", "sleep", "biometrics"]
                },
                metadata={"impact": "performance_optimization"},
                user_id="test_user"
            )
            
        elif event_type_choice < 0.7:  # 5% - Knowledge access (Neuroscientist domain expertise)
            event = AURENStreamEvent(
                event_id=str(uuid.uuid4()),
                trace_id=str(uuid.uuid4()),
                session_id=f"knowledge_{datetime.now().timestamp()}",
                timestamp=datetime.now(timezone.utc),
                event_type=AURENEventType.KNOWLEDGE_ACCESS,
                source_agent=agent_details,
                target_agent=None,
                payload={
                    "knowledge_domain": "neuroscience",
                    "topic": random.choice([
                        "autonomic_nervous_system",
                        "hrv_interpretation",
                        "cns_fatigue_markers",
                        "recovery_protocols",
                        "stress_adaptation"
                    ]),
                    "items_accessed": random.randint(1, 5),
                    "relevance_score": random.uniform(0.8, 1.0)
                },
                metadata={"source": "specialist_knowledge_base"},
                user_id="test_user"
            )
            
        else:  # 30% - Agent completion with performance metrics
            event = AURENStreamEvent(
                event_id=str(uuid.uuid4()),
                trace_id=str(uuid.uuid4()),
                session_id=f"session_{agent}_{datetime.now().timestamp()}",
                timestamp=datetime.now(timezone.utc),
                event_type=AURENEventType.AGENT_EXECUTION_COMPLETED,
                source_agent=agent_details,
                target_agent=None,
                payload={
                    "execution_result": "success" if random.random() > 0.05 else "error",
                    "output_type": random.choice([
                        "cns_analysis_complete",
                        "recovery_protocol_generated",
                        "performance_insights_delivered",
                        "fatigue_assessment_complete"
                    ]),
                    "output_length": random.randint(500, 2000),
                    "llm_calls_made": random.randint(2, 8),
                    "tools_used": random.randint(1, 3)
                },
                metadata={"session_duration_ms": random.randint(5000, 45000)},
                performance_metrics=AURENPerformanceMetrics(
                    latency_ms=random.randint(2000, 8000),
                    token_cost=random.uniform(0.05, 0.8),
                    memory_usage_mb=random.randint(100, 300),
                    cpu_percentage=random.randint(20, 70),
                    success=random.random() > 0.05,
                    agent_id=agent,
                    collaboration_depth=0,  # No collaboration - single agent
                    knowledge_items_accessed=random.randint(2, 15),
                    hypotheses_formed=random.randint(0, 3),
                    confidence_score=random.uniform(0.85, 0.98)
                ),
                user_id="test_user"
            )
        
        # Send the event through Redis!
        success = await redis_streamer.stream_event(event)
        
        if success:
            event_count += 1
            logger.info(f"✅ Sent {event.event_type.value} event #{event_count:04d} for {agent}")
        else:
            logger.error(f"❌ Failed to send event")
        
        # Control the rate - slightly slower for more realistic neuroscientist analysis
        await asyncio.sleep(random.uniform(0.5, 1.5))  # 0.5-2 events per second

if __name__ == "__main__":
    try:
        asyncio.run(send_live_events())
    except KeyboardInterrupt:
        logger.info("\n👋 Live event stream stopped") 