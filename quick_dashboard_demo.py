#!/usr/bin/env python3
"""Quick demo to generate events visible on the dashboards"""

import asyncio
import json
import redis.asyncio as redis
from datetime import datetime, timezone
import uuid

async def generate_demo_events():
    """Generate some demo events to show dashboard features"""
    
    # Connect to Redis
    client = redis.from_url("redis://localhost:6379")
    
    print("🚀 Generating demo events for dashboards...")
    
    # Generate different types of events
    events = [
        {
            "event_type": "agent_execution_started",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "payload": {"query": "Analyzing your HRV patterns..."},
            "performance_metrics": {"latency_ms": 125}
        },
        {
            "event_type": "tool_usage",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "payload": {"tool_name": "Biometric Analyzer", "estimated_cost": 0.0003},
            "performance_metrics": {"token_cost": 0.0003}
        },
        {
            "event_type": "memory_operation",
            "payload": {"operation": "store", "content": "HRV baseline established at 42ms"},
            "performance_metrics": {"success": True}
        },
        {
            "event_type": "hypothesis_event",
            "payload": {"status": "formed", "hypothesis": "Morning cold exposure improves HRV"},
            "performance_metrics": {"confidence_score": 0.85}
        },
        {
            "event_type": "agent_execution_completed",
            "source_agent": {"role": "Neuroscientist", "agent_id": "neuro_001"},
            "performance_metrics": {
                "latency_ms": 850,
                "token_cost": 0.0012,
                "success": True,
                "confidence_score": 0.92
            }
        }
    ]
    
    # Send events to Redis streams
    for i, event_data in enumerate(events):
        event_id = str(uuid.uuid4())
        
        # Add required fields
        event = {
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event_data
        }
        
        # Determine stream based on importance
        if event_data["event_type"] in ["agent_execution_started", "agent_execution_completed"]:
            stream = "auren:events:critical"
        else:
            stream = "auren:events:operational"
        
        # Add to Redis stream
        await client.xadd(stream, {"data": json.dumps(event)})
        
        print(f"  ✓ Generated {event_data['event_type']} event")
        
        # Small delay to show progression
        await asyncio.sleep(0.5)
    
    await client.close()
    print("\n✅ Demo events generated! Check your dashboards now.")
    print("\n📊 You should see:")
    print("  - Agent thinking animations")
    print("  - Cost counter increasing")
    print("  - Memory and hypothesis counts going up")
    print("  - Events flowing in the stream")

if __name__ == "__main__":
    asyncio.run(generate_demo_events()) 