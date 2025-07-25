#!/usr/bin/env python3
"""Generate specific event types to showcase dashboard features"""

import asyncio
import json
import redis.asyncio as redis
from datetime import datetime, timezone
import uuid
import sys

async def generate_specific_event(event_type: str):
    """Generate a specific type of event"""
    
    client = redis.from_url("redis://localhost:6379")
    
    events = {
        "thinking": {
            "event_type": "agent_execution_started",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "payload": {"query": "Analyzing complex biometric patterns..."},
            "performance_metrics": {"latency_ms": 125}
        },
        "memory": {
            "event_type": "memory_operation",
            "payload": {
                "operation": "store",
                "content": "Peak performance window identified: 9-11 AM",
                "confidence": 0.92
            },
            "performance_metrics": {"success": True}
        },
        "hypothesis": {
            "event_type": "hypothesis_event",
            "payload": {
                "status": "validated",
                "hypothesis": "Cold exposure before bed improves deep sleep by 23%",
                "evidence_count": 7,
                "confidence": 0.88
            },
            "performance_metrics": {"confidence_score": 0.88}
        },
        "cost": {
            "event_type": "agent_execution_completed",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "performance_metrics": {
                "latency_ms": 1250,
                "token_cost": 0.0045,
                "tokens_used": 1500,
                "success": True,
                "confidence_score": 0.95
            }
        },
        "error": {
            "event_type": "agent_execution_completed",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "performance_metrics": {
                "latency_ms": 850,
                "success": False,
                "error_type": "RateLimitError"
            }
        }
    }
    
    if event_type not in events:
        print(f"❌ Unknown event type: {event_type}")
        print(f"Available types: {', '.join(events.keys())}")
        return
    
    event_data = events[event_type]
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event_data
    }
    
    # Determine stream
    stream = "auren:events:critical" if "agent_execution" in event_data["event_type"] else "auren:events:operational"
    
    # Send to Redis
    await client.xadd(stream, {"data": json.dumps(event)})
    await client.aclose()
    
    print(f"✅ Generated {event_type} event!")
    print(f"📊 Check your dashboard to see the effect")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_specific_events.py [thinking|memory|hypothesis|cost|error]")
        sys.exit(1)
    
    asyncio.run(generate_specific_event(sys.argv[1])) 