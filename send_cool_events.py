#!/usr/bin/env python3
"""Send cool events to demonstrate the enhanced dashboard"""

import asyncio
import redis.asyncio as redis
import json
from datetime import datetime, timezone
import uuid
import random

async def send_cool_events():
    client = redis.from_url("redis://localhost:6379")
    print("🚀 Sending cool dashboard events...")
    
    # Initial thinking event
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": "cool_demo",
        "user_id": "demo_user",
        "event_type": "agent_execution_started",
        "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
        "payload": {"query": "Analyzing your complete health profile..."}
    }
    await client.xadd("auren:events:critical", {"data": json.dumps(event)})
    
    await asyncio.sleep(1)
    
    # Biometric analysis
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": "cool_demo", 
        "user_id": "demo_user",
        "event_type": "biometric_analysis",
        "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
        "payload": {
            "metrics_available": ["hrv", "stress", "sleep_efficiency", "recovery"],
            "current_values": {
                "hrv": 42,
                "stress": 6.8,
                "sleep_efficiency": 0.78,
                "recovery_score": 62
            }
        }
    }
    await client.xadd("auren:events:operational", {"data": json.dumps(event)})
    
    # Multiple quick events
    for i in range(10):
        event_type = random.choice([
            "conversation_event",
            "tool_usage", 
            "memory_operation",
            "hypothesis_event",
            "agent_execution_completed"
        ])
        
        if event_type == "conversation_event":
            event = {
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "cool_demo",
                "user_id": "demo_user",
                "event_type": event_type,
                "payload": {
                    "direction": "user_to_system",
                    "message": random.choice([
                        "How can I improve my recovery?",
                        "What's my stress trend?",
                        "Should I do cold therapy today?"
                    ])
                }
            }
        elif event_type == "tool_usage":
            event = {
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "cool_demo",
                "user_id": "demo_user",
                "event_type": event_type,
                "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
                "payload": {
                    "tool_name": random.choice(["HRV Analyzer", "Sleep Pattern Detector", "Recovery Calculator"]),
                    "estimated_cost": random.uniform(0.0001, 0.0005)
                },
                "performance_metrics": {"token_cost": random.uniform(0.0001, 0.0005)}
            }
        elif event_type == "memory_operation":
            event = {
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "cool_demo",
                "user_id": "demo_user",
                "event_type": event_type,
                "payload": {
                    "operation": "store",
                    "memory_type": "insight",
                    "content": f"Pattern discovered: Your HRV improves after morning meditation"
                }
            }
        elif event_type == "hypothesis_event":
            event = {
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "cool_demo",
                "user_id": "demo_user",
                "event_type": event_type,
                "payload": {
                    "status": "validated",
                    "hypothesis": "Cold exposure before bed improves deep sleep",
                    "confidence": 0.89
                }
            }
        else:  # agent_execution_completed
            event = {
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "cool_demo",
                "user_id": "demo_user",
                "event_type": event_type,
                "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
                "performance_metrics": {
                    "latency_ms": random.randint(500, 1200),
                    "token_cost": random.uniform(0.001, 0.003),
                    "success": True,
                    "confidence_score": random.uniform(0.85, 0.95)
                }
            }
        
        stream = "auren:events:critical" if event_type == "agent_execution_completed" else "auren:events:operational"
        await client.xadd(stream, {"data": json.dumps(event)})
        
        print(f"   ✨ Sent {event_type}")
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    await client.aclose()
    print("\n🎉 Dashboard should be showing activity now!")

if __name__ == "__main__":
    asyncio.run(send_cool_events()) 