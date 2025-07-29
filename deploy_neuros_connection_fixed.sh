#!/bin/bash
# NEUROS Connection Deployment Script - Fixed Version
# Connects NEUROS agent to chat messages in production

set -e

echo "🚀 NEUROS Connection Deployment (Fixed)"
echo "========================================"
echo "This will connect NEUROS to your chat messages"
echo ""

# Configuration
SERVER_IP="144.126.215.218"
SSH_PASS='.HvddX+@6dArsKd'
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "📦 Step 1: Creating deployment package..."

# Create temporary directory
mkdir -p /tmp/neuros_deploy_${TIMESTAMP}
cd /tmp/neuros_deploy_${TIMESTAMP}

# Copy NEUROS files
cp -r /Users/Jason/Downloads/CrewAI-Studio-main/auren/agents/neuros/* .

# Create the Kafka consumer
cat > kafka_consumer.py << 'EOF'
"""
NEUROS Kafka Consumer Service - Production Version
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any
from datetime import datetime
import uuid

from kafka import KafkaConsumer
import redis
import httpx

logging.basicConfig(
    level="INFO",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("neuros.kafka_consumer")

class NEUROSKafkaConsumer:
    def __init__(self):
        self.kafka_bootstrap = "kafka:9092"
        self.consumer_group = "neuros-chat-consumer"
        self.topic = "user-interactions"
        self.neuros_url = "http://neuros-api:8001"
        self.redis_url = "redis://redis:6379"
        self.redis_client = None
        self.http_client = httpx.Client(timeout=30.0)
        self.consumer = None
        
    def initialize(self):
        """Initialize connections"""
        try:
            # Initialize Redis
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
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
    
    def process_message(self, kafka_message: Dict[str, Any]):
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
                response = self.http_client.post(
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
                self.redis_client.publish(
                    redis_channel,
                    json.dumps(chat_response)
                )
                logger.info(f"Published response to Redis: {redis_channel}")
                
                # Also store in chat history
                history_key = f"chat:session:{session_id}:messages"
                self.redis_client.rpush(
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
                self.redis_client.expire(history_key, 7200)  # 2 hour TTL
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to call NEUROS API: {e}")
                self._send_error_response(session_id, "NEUROS is temporarily unavailable")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            if session_id:
                self._send_error_response(session_id, "Error processing your message")
    
    def _send_error_response(self, session_id: str, error_message: str):
        """Send error response to Redis"""
        try:
            error_response = {
                "type": "system",
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
            
            self.redis_client.publish(
                f"neuros:responses:{session_id}",
                json.dumps(error_response)
            )
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")
    
    def consume_messages(self):
        """Main consumer loop"""
        logger.info("Starting Kafka consumer loop...")
        
        while True:
            try:
                # Poll for messages
                raw_messages = self.consumer.poll(timeout_ms=1000)
                
                # Process each message
                for topic_partition, messages in raw_messages.items():
                    for message in messages:
                        self.process_message(message.value)
                        
            except Exception as e:
                logger.error(f"Error in consumer loop: {e}")
                import time
                time.sleep(5)
    
    def run(self):
        """Run the consumer service"""
        try:
            self.initialize()
            logger.info("NEUROS Kafka Consumer started successfully")
            self.consume_messages()
        except KeyboardInterrupt:
            logger.info("Shutting down NEUROS Kafka Consumer...")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            raise
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.consumer:
            self.consumer.close()
        if self.redis_client:
            self.redis_client.close()
        if self.http_client:
            self.http_client.close()
        logger.info("Cleanup completed")

def main():
    """Main entry point"""
    consumer = NEUROSKafkaConsumer()
    consumer.run()

if __name__ == "__main__":
    main()
EOF

# Create package
tar -czf neuros_deploy.tar.gz *

echo "✅ Package created"

echo ""
echo "🚀 Step 2: Deploying to production server..."

# Copy to server
sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=no \
    neuros_deploy.tar.gz \
    root@${SERVER_IP}:/root/

# Deploy on server
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no root@${SERVER_IP} << 'REMOTE_EOF'
cd /root

echo "📦 Creating directories and extracting..."
mkdir -p neuros_deploy
cd neuros_deploy
tar -xzf ../neuros_deploy.tar.gz

echo ""
echo "🏗️ Creating Dockerfiles..."

# Create NEUROS API Dockerfile
cat > Dockerfile.api << 'DOCKERFILE_EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY section_8_neuros_graph.py .
COPY main.py .
COPY neuros_agent_profile.yaml /config/

ENV POSTGRES_URL=postgresql://auren_user:auren_password_2024@postgres:5432/auren_production
ENV REDIS_URL=redis://redis:6379
ENV NEUROS_YAML_PATH=/config/neuros_agent_profile.yaml
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
DOCKERFILE_EOF

# Create Kafka Consumer Dockerfile
cat > Dockerfile.consumer << 'DOCKERFILE_EOF'
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir kafka-python redis httpx

COPY kafka_consumer.py .

ENV PYTHONUNBUFFERED=1

CMD ["python", "kafka_consumer.py"]
DOCKERFILE_EOF

echo ""
echo "🏗️ Building Docker images..."

docker build -f Dockerfile.api -t neuros-api:latest .
docker build -f Dockerfile.consumer -t neuros-consumer:latest .

echo ""
echo "🚀 Starting NEUROS services..."

# Stop any existing containers
docker stop neuros-api neuros-consumer 2>/dev/null || true
docker rm neuros-api neuros-consumer 2>/dev/null || true

# Start NEUROS API
docker run -d \
    --name neuros-api \
    --network auren-network \
    -p 8001:8001 \
    neuros-api:latest

# Start Kafka Consumer
docker run -d \
    --name neuros-consumer \
    --network auren-network \
    neuros-consumer:latest

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "🧪 Testing NEUROS API..."
curl -f http://localhost:8001/health || echo "❌ NEUROS API not responding yet"

echo ""
echo "📊 Checking service status..."
docker ps | grep neuros || echo "No NEUROS containers running"

echo ""
echo "📝 Checking logs..."
echo "=== NEUROS API Logs ==="
docker logs --tail 20 neuros-api 2>&1 || echo "No logs available"
echo ""
echo "=== NEUROS Consumer Logs ==="
docker logs --tail 20 neuros-consumer 2>&1 || echo "No logs available"

echo ""
echo "🔍 Checking for errors..."
docker logs neuros-api 2>&1 | grep -i error | tail -5 || echo "No errors found in API"
docker logs neuros-consumer 2>&1 | grep -i error | tail -5 || echo "No errors found in Consumer"

REMOTE_EOF

# Clean up
rm -rf /tmp/neuros_deploy_${TIMESTAMP}

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