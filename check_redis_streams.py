#!/usr/bin/env python3
"""Check Redis streams for events"""

import asyncio
import redis.asyncio as redis
import json

async def check_streams():
    client = redis.from_url("redis://localhost:6379")
    
    streams = ["auren:events:critical", "auren:events:operational", "auren:events:analytical"]
    
    for stream in streams:
        # Get stream length
        length = await client.xlen(stream)
        print(f"\n📊 {stream}: {length} events")
        
        # Get last 3 events
        if length > 0:
            events = await client.xrevrange(stream, count=3)
            print(f"   Latest events:")
            for event_id, data in events:
                event_data = json.loads(data[b'data'])
                print(f"   - {event_data.get('event_type', 'unknown')} at {event_data.get('timestamp', 'unknown')[:19]}")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(check_streams()) 