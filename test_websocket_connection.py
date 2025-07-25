#!/usr/bin/env python3
"""Test WebSocket connection"""

import asyncio
import websockets
import json

async def test_connection():
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")
            
            # Send subscription
            await websocket.send(json.dumps({
                "action": "subscribe",
                "filters": {"event_types": ["all"]}
            }))
            
            print("📡 Waiting for events...")
            
            # Listen for a few events
            for i in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    print(f"   📨 Received: {data.get('event_type', data.get('type', 'unknown'))}")
                except asyncio.TimeoutError:
                    print("   ⏱️  Timeout waiting for event")
                    
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection()) 