"""
Simple script to test WebSocket connection
"""

import asyncio
import websockets
import json

async def test_connection():
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")
            
            # Send authentication
            auth_message = {
                "token": "test-token-123",
                "agent_filter": [],
                "performance_threshold": 0.0,
                "subscriptions": ["all_events"]
            }
            
            await websocket.send(json.dumps(auth_message))
            print("✅ Sent authentication")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✅ Received: {data['type']}")
            
            if data.get("type") == "connection_established":
                print(f"✅ Connection ID: {data.get('connection_id')}")
                print("✅ WebSocket connection successful!")
                
                # Keep connection open to receive events
                print("\n📡 Listening for events (Ctrl+C to stop)...")
                while True:
                    message = await websocket.recv()
                    event = json.loads(message)
                    print(f"📨 Event: {event.get('type', 'unknown')} - {event.get('event', {}).get('event_type', '')}")
            else:
                print(f"❌ Unexpected response: {data}")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    print("Testing WebSocket connection...")
    try:
        asyncio.run(test_connection())
    except KeyboardInterrupt:
        print("\n✅ Test stopped") 