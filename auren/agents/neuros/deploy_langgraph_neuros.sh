#!/bin/bash

# NEUROS LangGraph Deployment Script
# Upgrades NEUROS to sophisticated LangGraph implementation

echo "=========================================="
echo "NEUROS LANGGRAPH DEPLOYMENT"
echo "Upgrading to sophisticated cognitive system"
echo "=========================================="

# Configuration
SERVER_IP="144.126.215.218"
SSH_PASS=".HvddX+@6dArsKd"
OPENAI_API_KEY="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"

echo "Step 1: Creating deployment package..."
cd auren/agents/neuros

# Create deployment tarball
tar -czf neuros_langgraph_deploy.tar.gz \
    neuros_langgraph.py \
    neuros_agent_profile.yaml \
    kafka_consumer.py \
    requirements.txt

echo "Step 2: Uploading to server..."
sshpass -p "$SSH_PASS" scp neuros_langgraph_deploy.tar.gz root@$SERVER_IP:/root/

echo "Step 3: Deploying on server..."
sshpass -p "$SSH_PASS" ssh root@$SERVER_IP << 'EOF'
cd /root

# Extract files
mkdir -p neuros_langgraph_deploy
tar -xzf neuros_langgraph_deploy.tar.gz -C neuros_langgraph_deploy/

# Update requirements for LangGraph
cat > neuros_langgraph_deploy/requirements_langgraph.txt << 'REQ'
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.5.3
redis==5.0.1
httpx==0.27.0
python-dotenv==1.0.0
openai==1.33.0
langgraph==0.2.56
langchain==0.3.17
langchain-openai==0.1.23
asyncpg==0.29.0
psycopg2-binary==2.9.10
pyyaml==6.0.1
REQ

# Create updated Dockerfile
cat > neuros_langgraph_deploy/Dockerfile.langgraph << 'DOCKER'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements_langgraph.txt .
RUN pip install --no-cache-dir -r requirements_langgraph.txt

# Copy application files
COPY neuros_langgraph.py .
COPY neuros_agent_profile.yaml .
COPY kafka_consumer.py .

# Run the LangGraph API
CMD ["uvicorn", "neuros_langgraph:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKER

# Build new image
echo "Building LangGraph NEUROS image..."
cd neuros_langgraph_deploy
docker build -f Dockerfile.langgraph -t neuros-langgraph:latest .

# Stop existing NEUROS containers
echo "Stopping existing NEUROS services..."
docker stop neuros-api neuros-consumer || true
docker rm neuros-api neuros-consumer || true

# Start new NEUROS LangGraph API
echo "Starting NEUROS LangGraph API..."
docker run -d \
  --name neuros-api \
  --network auren-network \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e REDIS_URL="redis://auren-redis:6379" \
  -e DATABASE_URL="postgresql://auren_user:auren_secure_2025@auren-postgres:5432/auren_production" \
  -e LOG_LEVEL="INFO" \
  --restart unless-stopped \
  neuros-langgraph:latest

# Update Kafka consumer to use new API
echo "Updating Kafka consumer..."
docker run -d \
  --name neuros-consumer \
  --network auren-network \
  -e NEUROS_API_URL="http://neuros-api:8000" \
  -e KAFKA_BOOTSTRAP_SERVERS="auren-kafka:9092" \
  -e REDIS_URL="redis://auren-redis:6379" \
  -e LOG_LEVEL="INFO" \
  --restart unless-stopped \
  neuros-consumer:latest

echo "Waiting for services to start..."
sleep 10

# Verify deployment
echo "Verifying deployment..."
docker ps | grep neuros

# Test health endpoint
echo "Testing NEUROS LangGraph health..."
curl -s http://localhost:8000/health | jq .

echo "Testing cognitive modes..."
curl -s http://localhost:8000/modes | jq .

echo "=========================================="
echo "NEUROS LANGGRAPH DEPLOYMENT COMPLETE!"
echo "=========================================="
EOF

# Set environment variable with API key
sshpass -p "$SSH_PASS" ssh root@$SERVER_IP "echo 'export OPENAI_API_KEY=\"$OPENAI_API_KEY\"' >> /root/.bashrc"

echo "Step 4: Testing from local machine..."
echo "Testing chat endpoint with sophisticated NEUROS..."
curl -X POST http://$SERVER_IP:8888/api/chat/neuros \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I have been feeling stressed lately and my sleep has been disrupted. What patterns do you see?",
    "session_id": "langgraph-test"
  }' | jq .

echo ""
echo "Deployment complete! NEUROS is now running with:"
echo "- Full LangGraph cognitive state machine"
echo "- 6 operational modes with dynamic switching"
echo "- Three-tier memory system (L1/L2/L3)"
echo "- OpenAI GPT-4 integration"
echo "- Pattern synthesis and hypothesis generation"
echo "- Complete YAML personality implementation"
echo ""
echo "Access NEUROS at: http://$SERVER_IP:8888/api/chat/neuros" 