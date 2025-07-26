"""
Monitor what events the dashboard is receiving
"""

import asyncio
import websockets
import json
from datetime import datetime

async def monitor():
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Send authentication
            auth_message = {
                "token": "test-token-123",
                "agent_filter": [],
                "performance_threshold": 0.0,
                "subscriptions": ["all_events"]
            }
            
            await websocket.send(json.dumps(auth_message))
            print("✅ Sent authentication")
            
            # Monitor events
            event_count = 0
            event_types = {}
            
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    if data.get("type") == "stream_event":
                        event = data.get("event", {})
                        event_type = event.get("event_type", "unknown")
                        
                        event_count += 1
                        event_types[event_type] = event_types.get(event_type, 0) + 1
                        
                        # Print summary every 10 events
                        if event_count % 10 == 0:
                            print(f"\n📊 Event Summary (Total: {event_count})")
                            for evt_type, count in event_types.items():
                                print(f"  - {evt_type}: {count}")
                        
                        # Print specific interesting events
                        if event_type in ["agent_collaboration", "memory_tier_access"]:
                            print(f"\n🔥 {event_type}: {json.dumps(event.get('payload', {}), indent=2)}")
                    
                    elif data.get("type") == "connection_established":
                        print(f"✅ Connection established: {data}")
                    
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(monitor()) 