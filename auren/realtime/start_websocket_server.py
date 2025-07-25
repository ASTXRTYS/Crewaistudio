"""
Start the WebSocket server with proper Redis integration
This ensures events flow from Redis to the dashboard
"""

import asyncio
import logging
from auren.realtime.enhanced_websocket_streamer import EnhancedWebSocketEventStreamer
from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Start WebSocket server with Redis event streaming"""
    
    # Create Redis event streamer
    redis_streamer = RedisStreamEventStreamer(
        redis_url="redis://localhost:6379",
        stream_name="auren:events"
    )
    await redis_streamer.initialize()
    logger.info("✅ Redis streamer initialized")
    
    # Create WebSocket server with Redis integration
    websocket_server = EnhancedWebSocketEventStreamer(
        host="localhost",
        port=8765,
        event_streamer=redis_streamer,  # This connects WebSocket to Redis!
        max_connections=1000
    )
    
    logger.info("🚀 Starting WebSocket server with Redis integration on port 8765...")
    
    # Start the server
    await websocket_server.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 WebSocket server stopped") 