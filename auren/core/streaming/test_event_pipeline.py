"""
Test script to verify the Module C event pipeline
Tests: Instrumentation → Redis Streaming → WebSocket Server
"""

import asyncio
import logging
from datetime import datetime, timezone
from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer as CrewAIEventInstrumentation

from auren.realtime.langgraph_instrumentation import (
    CrewAIEventInstrumentation, 
    AURENStreamEvent, 
    AURENEventType,
    AURENPerformanceMetrics
)
from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer
from auren.realtime.enhanced_websocket_streamer import EnhancedWebSocketEventStreamer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_event_pipeline():
    """Test the complete event pipeline"""
    
    # 1. Initialize Redis Streamer
    redis_streamer = RedisStreamEventStreamer(
        redis_url="redis://localhost:6379",
        stream_name="auren:test:events"
    )
    await redis_streamer.initialize()
    logger.info("✅ Redis streamer initialized")
    
    # 2. Initialize CrewAI Instrumentation
    instrumentation = CrewAIEventInstrumentation(
        event_streamer=redis_streamer
    )
    logger.info("✅ CrewAI instrumentation initialized")
    
    # 3. Create and send test events
    test_events = [
        # Agent execution start
        AURENStreamEvent(
            event_id="test_001",
            trace_id="trace_001",
            session_id="session_001",
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.AGENT_EXECUTION_STARTED,
            source_agent={
                "id": "neuroscientist",
                "role": "Neuroscientist",
                "goal": "Analyze biometric patterns"
            },
            target_agent=None,
            payload={
                "execution_mode": "autonomous",
                "tools_available": 3
            },
            metadata={
                "test": True,
                "pipeline_test": "Module C"
            }
        ),
        
        # LLM call event
        AURENStreamEvent(
            event_id="test_002",
            trace_id="trace_001",
            session_id="session_001",
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.LLM_CALL,
            source_agent={
                "id": "neuroscientist",
                "role": "Neuroscientist"
            },
            target_agent=None,
            payload={
                "model": "gpt-4",
                "tokens_used": 500,
                "cost": 0.015,
                "success": True
            },
            metadata={
                "provider": "openai"
            }
        ),
        
        # Agent collaboration event
        AURENStreamEvent(
            event_id="test_003",
            trace_id="trace_002",
            session_id="session_002",
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.AGENT_COLLABORATION,
            source_agent={
                "id": "neuroscientist",
                "role": "Neuroscientist"
            },
            target_agent=None,
            payload={
                "primary_agent": "neuroscientist",
                "collaborating_agents": ["sleep_specialist", "recovery_coach"],
                "collaboration_type": "sleep_analysis",
                "consensus_reached": True,
                "confidence_scores": {
                    "neuroscientist": 0.85,
                    "sleep_specialist": 0.78,
                    "recovery_coach": 0.82
                }
            },
            metadata={
                "domains_involved": ["neuroscience", "sleep", "recovery"]
            }
        ),
        
        # Performance metric event
        AURENStreamEvent(
            event_id="test_004",
            trace_id="trace_001",
            session_id="session_001",
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.AGENT_EXECUTION_COMPLETED,
            source_agent={
                "id": "neuroscientist",
                "role": "Neuroscientist"
            },
            target_agent=None,
            payload={
                "execution_result": "success",
                "output_length": 256
            },
            metadata={
                "session_duration_ms": 1500
            },
            performance_metrics=AURENPerformanceMetrics(
                latency_ms=1500,
                token_cost=0.015,
                memory_usage_mb=125.5,
                cpu_percentage=15.2,
                success=True,
                agent_id="neuroscientist",
                confidence_score=0.85
            )
        )
    ]
    
    # Send test events
    for event in test_events:
        success = await redis_streamer.stream_event(event)
        if success:
            logger.info(f"✅ Sent event: {event.event_type.value} - {event.event_id}")
        else:
            logger.error(f"❌ Failed to send event: {event.event_id}")
    
    # 4. Test reading recent events
    recent_events = await redis_streamer.get_recent_events(limit=10)
    logger.info(f"✅ Retrieved {len(recent_events)} recent events")
    
    # 5. Test WebSocket server initialization (without actually starting it)
    websocket_server = EnhancedWebSocketEventStreamer(
        host="localhost",
        port=8765,
        event_streamer=redis_streamer
    )
    logger.info("✅ WebSocket server configured")
    
    return {
        "redis_connected": True,
        "events_sent": len(test_events),
        "events_retrieved": len(recent_events),
        "websocket_ready": True
    }


async def test_event_subscription():
    """Test event subscription from Redis"""
    
    redis_streamer = RedisStreamEventStreamer(
        redis_url="redis://localhost:6379",
        stream_name="auren:test:events"
    )
    await redis_streamer.initialize()
    
    logger.info("Starting event subscription test...")
    
    # Subscribe and read a few events
    event_count = 0
    async for event in redis_streamer.subscribe_to_events("test_consumer"):
        logger.info(f"Received event: {event.get('event_type')} - {event.get('event_id')}")
        event_count += 1
        
        # Stop after receiving 3 events
        if event_count >= 3:
            break
    
    logger.info(f"✅ Successfully subscribed and received {event_count} events")


if __name__ == "__main__":
    # Run pipeline test
    logger.info("=== Testing Module C Event Pipeline ===")
    result = asyncio.run(test_event_pipeline())
    
    logger.info("\n=== Pipeline Test Results ===")
    for key, value in result.items():
        logger.info(f"{key}: {value}")
    
    # Optional: Test subscription (this will wait for events)
    # asyncio.run(test_event_subscription()) 