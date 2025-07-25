#!/usr/bin/env python3
"""Send a test event to verify dashboard connectivity"""

import asyncio
import redis.asyncio as redis
import json
from datetime import datetime, timezone
import uuid

async def send_test_event():
    client = redis.from_url("redis://localhost:6379")
    
    # Send a critical agent event
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": "test_session",
        "user_id": "test_user",
        "event_type": "agent_execution_started",
        "source_agent": {
            "role": "Neuroscientist",
            "agent_id": "neuro_test"
        },
        "payload": {
            "query": "TEST: Dashboard connectivity check! If you see this, it's working!",
            "context": "Testing real-time event streaming"
        },
        "performance_metrics": {
            "latency_ms": 123
        }
    }
    
    # Send to critical stream
    await client.xadd("auren:events:critical", {"data": json.dumps(event)})
    print("✅ Sent test event to critical stream")
    
    # Send a conversation event
    conv_event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": "test_session",
        "user_id": "test_user",
        "event_type": "conversation_event",
        "payload": {
            "direction": "user_to_system",
            "message": "Hello AUREN! Testing dashboard connectivity!",
            "conversation_id": 1
        }
    }
    
    await client.xadd("auren:events:operational", {"data": json.dumps(conv_event)})
    print("✅ Sent conversation event to operational stream")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(send_test_event()) 