#!/bin/bash
# NEUROS Connection Deployment Script
# Connects NEUROS agent to chat messages in production

set -e

echo "🚀 NEUROS Connection Deployment"
echo "================================"
echo "This will connect NEUROS to your chat messages"
echo ""

# Configuration
SERVER_IP="144.126.215.218"
SSH_PASS='.HvddX+@6dArsKd'
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "📦 Step 1: Creating production-ready Kafka consumer..."

# Update Kafka consumer with production settings
cat > CrewAI-Studio-main/auren/agents/neuros/kafka_consumer_prod.py << 'EOF'
"""
NEUROS Kafka Consumer Service - Production Version
Bridges chat messages from Kafka to NEUROS cognitive processing
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from kafka import KafkaConsumer
from kafka.errors import KafkaError
import redis.asyncio as redis
import httpx

# Configure logging
logging.basicConfig(
    level="INFO",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("neuros.kafka_consumer")

class NEUROSKafkaConsumer:
    """Consumes chat messages from Kafka and routes to NEUROS"""
    
    def __init__(self):
        # Production Kafka configuration
        self.kafka_bootstrap = "kafka:9092"
        self.consumer_group = "neuros-chat-consumer"
        self.topic = "user-interactions"
        
        # NEUROS API configuration (running in same container network)
        self.neuros_url = "http://neuros-api:8001"
        
        # Redis configuration
        self.redis_url = "redis://redis:6379"
        self.redis_client = None
        
        # HTTP client for NEUROS API
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Kafka consumer
        self.consumer = None
        
    async def initialize(self):
        """Initialize connections"""
        try:
            # Initialize Redis
            self.redis_client = await redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis connection established")
            
            # Initialize Kafka consumer
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.kafka_bootstrap,
                group_id=self.consumer_group,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                max_poll_records=10
            )
            logger.info(f"Kafka consumer initialized for topic: {self.topic}")
            
        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}")
            raise
    
    async def process_message(self, kafka_message: Dict[str, Any]):
        """Process a single message from Kafka"""
        try:
            # Extract message details
            event_type = kafka_message.get("event_type", "user.message")
            user_id = kafka_message.get("user_id", "pwa_user")
            session_id = kafka_message.get("session_id")
            message_data = kafka_message.get("message", {})
            text = message_data.get("text", "")
            
            if not text or not session_id:
                logger.warning("Skipping message without text or session_id")
                return
            
            logger.info(f"Processing message from {user_id}: {text[:50]}...")
            
            # Create biometric event for NEUROS
            biometric_event = {
                "event_type": "conversation.message",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "message": text,
                    "session_id": session_id,
                    "context": message_data.get("context", {}),
                    "source": "pwa_chat"
                },
                "thread_id": session_id
            }
            
            # Call NEUROS API
            try:
                response = await self.http_client.post(
                    f"{self.neuros_url}/process",
                    json=biometric_event
                )
                response.raise_for_status()
                neuros_response = response.json()
                
                logger.info(f"NEUROS response: mode={neuros_response.get('mode')}, "
                          f"thread={neuros_response.get('thread_id')}")
                
                # Format response for chat
                chat_response = {
                    "type": "agent_response",
                    "response": neuros_response.get("response", "I'm processing that information."),
                    "agent_id": "neuros",
                    "mode": neuros_response.get("mode", "BASELINE"),
                    "timestamp": datetime.now().isoformat(),
                    "metadata": neuros_response.get("metadata", {})
                }
                
                # Publish to Redis for WebSocket/API pickup
                redis_channel = f"neuros:responses:{session_id}"
                await self.redis_client.publish(
                    redis_channel,
                    json.dumps(chat_response)
                )
                logger.info(f"Published response to Redis: {redis_channel}")
                
                # Also store in chat history
                history_key = f"chat:session:{session_id}:messages"
                await self.redis_client.rpush(
                    history_key,
                    json.dumps({
                        "id": str(uuid.uuid4()),
                        "text": chat_response["response"],
                        "sender": "agent",
                        "agent": "neuros",
                        "timestamp": chat_response["timestamp"],
                        "mode": chat_response["mode"]
                    })
                )
                await self.redis_client.expire(history_key, 7200)  # 2 hour TTL
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to call NEUROS API: {e}")
                await self._send_error_response(session_id, "NEUROS is temporarily unavailable")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            if session_id:
                await self._send_error_response(session_id, "Error processing your message")
    
    async def _send_error_response(self, session_id: str, error_message: str):
        """Send error response to Redis"""
        try:
            error_response = {
                "type": "system",
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.publish(
                f"neuros:responses:{session_id}",
                json.dumps(error_response)
            )
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")
    
    async def consume_messages(self):
        """Main consumer loop"""
        logger.info("Starting Kafka consumer loop...")
        
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                # Poll for messages
                raw_messages = await loop.run_in_executor(
                    None, 
                    lambda: self.consumer.poll(timeout_ms=1000)
                )
                
                # Process each message
                for topic_partition, messages in raw_messages.items():
                    for message in messages:
                        await self.process_message(message.value)
                        
            except Exception as e:
                logger.error(f"Error in consumer loop: {e}")
                await asyncio.sleep(5)
    
    async def run(self):
        """Run the consumer service"""
        try:
            await self.initialize()
            logger.info("NEUROS Kafka Consumer started successfully")
            await self.consume_messages()
        except KeyboardInterrupt:
            logger.info("Shutting down NEUROS Kafka Consumer...")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        if self.consumer:
            self.consumer.close()
        if self.redis_client:
            await self.redis_client.close()
        if self.http_client:
            await self.http_client.aclose()
        logger.info("Cleanup completed")

async def main():
    """Main entry point"""
    consumer = NEUROSKafkaConsumer()
    await consumer.run()

if __name__ == "__main__":
    asyncio.run(main())
EOF

echo "✅ Kafka consumer ready"

echo ""
echo "📦 Step 2: Creating deployment package..."

# Package everything
cd CrewAI-Studio-main/auren/agents/neuros
tar -czf neuros_deployment_${TIMESTAMP}.tar.gz \
    main.py \
    section_8_neuros_graph.py \
    neuros_agent_profile.yaml \
    requirements.txt \
    kafka_consumer_prod.py

echo "✅ Package created"

echo ""
echo "🚀 Step 3: Deploying to production server..."

# Copy to server
sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=no \
    neuros_deployment_${TIMESTAMP}.tar.gz \
    root@${SERVER_IP}:/root/

# Deploy on server
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no root@${SERVER_IP} << 'REMOTE_EOF'
cd /root
echo "📦 Extracting deployment package..."
mkdir -p /root/auren-production/auren/agents/neuros/
tar -xzf neuros_deployment_*.tar.gz -C /root/auren-production/auren/agents/neuros/

cd /root/auren-production

echo ""
echo "🏗️ Creating Docker setup..."

# Create NEUROS API Dockerfile
cat > auren/agents/neuros/Dockerfile.prod << 'DOCKERFILE_EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY section_8_neuros_graph.py .
COPY main.py .

# Copy YAML configuration
COPY neuros_agent_profile.yaml /config/

# Environment variables
ENV POSTGRES_URL=postgresql://auren_user:auren_password_2024@postgres:5432/auren_production
ENV REDIS_URL=redis://redis:6379
ENV NEUROS_YAML_PATH=/config/neuros_agent_profile.yaml
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["python", "main.py"]
DOCKERFILE_EOF

# Create Kafka Consumer Dockerfile
cat > auren/agents/neuros/Dockerfile.consumer << 'DOCKERFILE_EOF'
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    kafka-python \
    redis \
    httpx \
    python-dotenv

COPY kafka_consumer_prod.py kafka_consumer.py

ENV PYTHONUNBUFFERED=1

CMD ["python", "kafka_consumer.py"]
DOCKERFILE_EOF

echo ""
echo "🏗️ Building Docker images..."

# Build NEUROS API image
docker build -f auren/agents/neuros/Dockerfile.prod \
    -t auren/neuros-api:latest \
    auren/agents/neuros/

# Build Kafka consumer image
docker build -f auren/agents/neuros/Dockerfile.consumer \
    -t auren/neuros-consumer:latest \
    auren/agents/neuros/

echo ""
echo "🚀 Starting NEUROS services..."

# Stop any existing NEUROS containers
docker stop neuros-api neuros-consumer 2>/dev/null || true
docker rm neuros-api neuros-consumer 2>/dev/null || true

# Start NEUROS API
docker run -d \
    --name neuros-api \
    --network auren-network \
    -p 8001:8001 \
    -e POSTGRES_URL=postgresql://auren_user:auren_password_2024@postgres:5432/auren_production \
    -e REDIS_URL=redis://redis:6379 \
    -v /root/auren-production/auren/agents/neuros/neuros_agent_profile.yaml:/config/neuros_agent_profile.yaml:ro \
    auren/neuros-api:latest

# Start Kafka Consumer
docker run -d \
    --name neuros-consumer \
    --network auren-network \
    auren/neuros-consumer:latest

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "🧪 Testing NEUROS API..."
curl -f http://localhost:8001/health || echo "❌ NEUROS API not responding"

echo ""
echo "📊 Checking service status..."
docker ps | grep neuros

echo ""
echo "📝 Checking logs..."
echo "=== NEUROS API Logs ==="
docker logs --tail 20 neuros-api
echo ""
echo "=== NEUROS Consumer Logs ==="
docker logs --tail 20 neuros-consumer

REMOTE_EOF

# Clean up local package
rm neuros_deployment_${TIMESTAMP}.tar.gz
cd ../../../..

echo ""
echo "✅ NEUROS Connection Deployment Complete!"
echo ""
echo "🎯 What happens now:"
echo "1. When you send a message in the PWA, it goes to Kafka"
echo "2. NEUROS Consumer picks it up and sends to NEUROS API"
echo "3. NEUROS processes with its cognitive modes"
echo "4. Response is published to Redis"
echo "5. Your PWA receives the response!"
echo ""
echo "🧪 Test it by sending a message in your PWA!"
echo "📊 Monitor with: sshpass -p '$SSH_PASS' ssh root@$SERVER_IP 'docker logs -f neuros-consumer'"
echo "" 