#!/usr/bin/env python3
"""Simple WebSocket server for AUREN dashboard"""

import asyncio
import websockets
import redis.asyncio as redis
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleWebSocketServer:
    def __init__(self):
        self.clients = set()
        self.redis_client = None
        
    async def start(self):
        """Start the WebSocket server"""
        self.redis_client = redis.from_url("redis://localhost:6379")
        logger.info("Connected to Redis")
        
        # Start Redis stream readers
        asyncio.create_task(self.read_redis_streams())
        
        # Start WebSocket server
        logger.info("Starting WebSocket server on port 8765...")
        async with websockets.serve(self.handle_client, "localhost", 8765):
            logger.info("WebSocket server started! Waiting for connections...")
            await asyncio.Future()  # Run forever
    
    async def handle_client(self, websocket):
        """Handle a WebSocket client connection"""
        logger.info(f"New client connected from {websocket.remote_address}")
        self.clients.add(websocket)
        
        try:
            # Send initial connection success
            await websocket.send(json.dumps({
                "type": "connection",
                "status": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            # Keep connection alive
            async for message in websocket:
                # Handle any client messages (like subscriptions)
                logger.info(f"Received from client: {message}")
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        finally:
            self.clients.remove(websocket)
    
    async def read_redis_streams(self):
        """Read from Redis streams and forward to WebSocket clients"""
        streams = {
            "auren:events:critical": "$",
            "auren:events:operational": "$",
            "auren:events:analytical": "$"
        }
        
        logger.info("Starting Redis stream reader...")
        
        while True:
            try:
                # Read from all streams
                result = await self.redis_client.xread(streams, block=1000)
                
                for stream_name, messages in result:
                    stream_name = stream_name.decode('utf-8')
                    
                    for msg_id, data in messages:
                        # Parse the event data
                        event_data = json.loads(data[b'data'])
                        
                        # Forward to all connected clients
                        if self.clients:
                            logger.info(f"Forwarding {event_data.get('event_type')} to {len(self.clients)} clients")
                            
                            # Send to all clients
                            disconnected = set()
                            for client in self.clients:
                                try:
                                    await client.send(json.dumps(event_data))
                                except:
                                    disconnected.add(client)
                            
                            # Remove disconnected clients
                            self.clients -= disconnected
                        
                        # Update stream position
                        streams[stream_name] = msg_id.decode('utf-8')
                
            except Exception as e:
                logger.error(f"Error reading Redis streams: {e}")
                await asyncio.sleep(1)

async def main():
    server = SimpleWebSocketServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main()) 