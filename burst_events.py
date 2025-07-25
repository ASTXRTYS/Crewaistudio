#!/usr/bin/env python3
"""Send a burst of events to make dashboard activity visible"""

import asyncio
import redis.asyncio as redis
import json
from datetime import datetime, timezone
import uuid

async def send_burst():
    client = redis.from_url("redis://localhost:6379")
    
    print("🚀 Sending burst of events...")
    
    # Send 5 quick conversations
    for i in range(5):
        # User message
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "burst_demo",
            "user_id": "demo_user",
            "event_type": "conversation_event",
            "payload": {
                "direction": "user_to_system",
                "message": f"Burst test message {i+1}: How can I improve my HRV?",
                "conversation_id": i+1
            }
        }
        await client.xadd("auren:events:operational", {"data": json.dumps(event)})
        
        # Agent thinking
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "burst_demo",
            "user_id": "demo_user",
            "event_type": "agent_execution_started",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "payload": {"query": f"Analyzing HRV improvement strategies #{i+1}"}
        }
        await client.xadd("auren:events:critical", {"data": json.dumps(event)})
        
        # Tool usage
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "burst_demo",
            "user_id": "demo_user",
            "event_type": "tool_usage",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "payload": {
                "tool_name": "HRV Pattern Analyzer",
                "estimated_cost": 0.0003
            },
            "performance_metrics": {"token_cost": 0.0003}
        }
        await client.xadd("auren:events:operational", {"data": json.dumps(event)})
        
        # Agent complete
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "burst_demo",
            "user_id": "demo_user",
            "event_type": "agent_execution_completed",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "performance_metrics": {
                "latency_ms": 850,
                "token_cost": 0.002,
                "tokens_used": 150,
                "success": True,
                "confidence_score": 0.92
            }
        }
        await client.xadd("auren:events:critical", {"data": json.dumps(event)})
        
        print(f"   ✅ Sent conversation {i+1}")
        await asyncio.sleep(0.5)
    
    # Send some memories
    for i in range(3):
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "burst_demo",
            "user_id": "demo_user",
            "event_type": "memory_operation",
            "payload": {
                "operation": "store",
                "memory_type": "insight",
                "content": f"Key insight #{i+1}: HRV improves with consistent practice",
                "confidence": 0.9
            }
        }
        await client.xadd("auren:events:operational", {"data": json.dumps(event)})
        print(f"   💾 Sent memory {i+1}")
    
    await client.aclose()
    print("\n✨ Burst complete! Check your dashboard now!")

if __name__ == "__main__":
    asyncio.run(send_burst()) 