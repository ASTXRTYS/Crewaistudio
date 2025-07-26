#!/usr/bin/env python3
"""
Test script for Knowledge Graph API integration
Tests that the API can fetch data from all three memory tiers
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_knowledge_graph_api():
    """Test the knowledge graph API endpoints"""
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("=== Testing Knowledge Graph API ===\n")
        
        # Test 1: Health check
        print("1. Testing API health...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"✓ API is healthy: {health['status']}")
                    print(f"  Components: {list(health['components'].keys())}")
                else:
                    print(f"✗ API health check failed: {response.status}")
        except Exception as e:
            print(f"✗ Failed to connect to API: {e}")
            return
        
        # Test 2: Memory stats
        print("\n2. Testing memory stats endpoint...")
        try:
            async with session.get(f"{base_url}/api/memory/stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"✓ Memory stats retrieved:")
                    print(f"  Total memories: {stats['overview']['total_memories']}")
                    print(f"  Hot tier: {stats['tiers']['hot']['memories']} memories")
                    print(f"  Warm tier: {stats['tiers']['warm']['memories']} memories")
                    print(f"  Cold tier: {stats['tiers']['cold']['memories']} memories")
                else:
                    print(f"✗ Memory stats failed: {response.status}")
        except Exception as e:
            print(f"✗ Failed to get memory stats: {e}")
        
        # Test 3: Knowledge graph data - Depth 1 (Hot tier only)
        print("\n3. Testing knowledge graph data (depth=1)...")
        try:
            async with session.get(
                f"{base_url}/api/knowledge-graph/data",
                params={"agent_id": "neuroscientist", "depth": 1}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Knowledge graph data (depth=1):")
                    print(f"  Nodes: {len(data['nodes'])}")
                    print(f"  Edges: {len(data['edges'])}")
                    print(f"  Stats: {data['stats']}")
                    
                    # Show sample nodes
                    if data['nodes']:
                        print("\n  Sample nodes:")
                        for node in data['nodes'][:3]:
                            print(f"    - {node['id'][:20]}... [{node['tier']}] {node['type']}")
                            print(f"      Content: {node['content'][:50]}...")
                else:
                    print(f"✗ Knowledge graph request failed: {response.status}")
                    error_text = await response.text()
                    print(f"  Error: {error_text}")
        except Exception as e:
            print(f"✗ Failed to get knowledge graph data: {e}")
        
        # Test 4: Knowledge graph data - Depth 2 (Hot + Warm)
        print("\n4. Testing knowledge graph data (depth=2)...")
        try:
            async with session.get(
                f"{base_url}/api/knowledge-graph/data",
                params={"agent_id": "neuroscientist", "depth": 2}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Knowledge graph data (depth=2):")
                    print(f"  Total nodes: {len(data['nodes'])}")
                    print(f"  Hot tier: {data['stats']['hot_tier_count']}")
                    print(f"  Warm tier: {data['stats']['warm_tier_count']}")
                    print(f"  User context nodes: {data['stats']['user_context_count']}")
                else:
                    print(f"✗ Knowledge graph request failed: {response.status}")
        except Exception as e:
            print(f"✗ Failed to get knowledge graph data: {e}")
        
        # Test 5: Knowledge access reporting
        print("\n5. Testing knowledge access reporting...")
        try:
            async with session.post(
                f"{base_url}/api/knowledge-graph/access",
                json={
                    "agent_id": "neuroscientist",
                    "memory_id": "test-memory-123",
                    "tier": "hot"
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✓ Knowledge access reported: {result['status']}")
                else:
                    print(f"✗ Knowledge access report failed: {response.status}")
        except Exception as e:
            print(f"✗ Failed to report knowledge access: {e}")
        
        # Test 6: WebSocket connection
        print("\n6. Testing WebSocket connection...")
        try:
            ws_url = f"ws://localhost:8000/ws/dashboard/test_user"
            async with session.ws_connect(ws_url) as ws:
                print(f"✓ WebSocket connected")
                
                # Send ping
                await ws.send_json({"type": "ping"})
                
                # Wait for messages with timeout
                try:
                    msg = await asyncio.wait_for(ws.receive(), timeout=2.0)
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        print(f"  Received: {data['type']}")
                except asyncio.TimeoutError:
                    print("  No messages received (timeout)")
                
                await ws.close()
        except Exception as e:
            print(f"✗ WebSocket connection failed: {e}")
        
        print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_graph_api()) 