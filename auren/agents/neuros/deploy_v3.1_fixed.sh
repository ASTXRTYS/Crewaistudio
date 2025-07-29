#!/bin/bash

# NEUROS v3.1 Fixed Deployment Script
# Deploys NEUROS with biometric triggers and protocol stacks

echo "=========================================="
echo "NEUROS v3.1 FIXED DEPLOYMENT"
echo "Incremental implementation with biometric triggers"
echo "=========================================="

# Configuration
SERVER_IP="144.126.215.218"
SSH_PASS=".HvddX+@6dArsKd"

echo "Step 1: Creating deployment package..."

# Temporarily copy the yaml file to the packaging directory
cp config/agents/neuros_agent_profile.yaml auren/agents/neuros/

# Change to the correct directory to package files
cd auren/agents/neuros

tar -czf ../../../neuros_v3.1_fixed.tar.gz \
    neuros_langgraph_v3.1_fixed.py \
    neuros_agent_profile.yaml \
    requirements_v3.1_fixed.txt

# Go back to project root and clean up
cd ../../..
rm auren/agents/neuros/neuros_agent_profile.yaml


echo "Step 2: Uploading to server..."
sshpass -p "$SSH_PASS" scp neuros_v3.1_fixed.tar.gz root@$SERVER_IP:/root/

echo "Step 3: Deploying on server..."
sshpass -p "$SSH_PASS" ssh root@$SERVER_IP << 'EOF'
cd /root

# Extract files
echo "Extracting deployment package..."
mkdir -p neuros_v31_deploy
tar -xzf neuros_v3.1_fixed.tar.gz -C neuros_v31_deploy/

# Copy the YAML profile from existing deployment
echo "Copying YAML profile..."
cp /root/neuros_langgraph_deploy/neuros_agent_profile.yaml neuros_v31_deploy/ || \
cp /root/neuros_deployment/neuros_agent_profile.yaml neuros_v31_deploy/ || \
echo "Warning: Could not find YAML profile"

# Rename files for consistency
cd neuros_v31_deploy
mv neuros_langgraph_v3.1_fixed.py neuros_langgraph.py
mv requirements_v3.1_fixed.txt requirements.txt

# Create Dockerfile
cat > Dockerfile << 'DOCKER'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY neuros_langgraph.py .
COPY neuros_agent_profile.yaml .

# Run the LangGraph API
CMD ["uvicorn", "neuros_langgraph:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKER

# Build new image
echo "Building NEUROS v3.1 image..."
docker build -t neuros-v31:latest .

# Stop any existing NEUROS containers
echo "Stopping existing NEUROS services..."
docker stop neuros-api neuros-consumer neuros-langgraph || true
docker rm neuros-api neuros-consumer neuros-langgraph || true

# Start new NEUROS v3.1
echo "Starting NEUROS v3.1..."
docker run -d \
  --name neuros-langgraph \
  --network auren-network \
  -p 8000:8000 \
  -e OPENAI_API_KEY="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" \
  -e REDIS_URL="redis://auren-redis:6379" \
  -e DATABASE_URL="postgresql://auren_user:auren_secure_2025@auren-postgres:5432/auren_production" \
  -e KAFKA_BOOTSTRAP_SERVERS="auren-kafka:9092" \
  -e LOG_LEVEL="INFO" \
  --restart unless-stopped \
  neuros-v31:latest

echo "Waiting for service to start..."
sleep 10

# Verify deployment
echo "Verifying deployment..."
docker ps | grep neuros

# Test health endpoint
echo ""
echo "Testing NEUROS v3.1 health..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Health check failed"

echo ""
echo "Testing available modes..."
curl -s http://localhost:8000/modes | python3 -m json.tool || echo "Modes check failed"

echo ""
echo "Testing protocol stacks..."
curl -s http://localhost:8000/protocols | python3 -m json.tool || echo "Protocols check failed"

echo ""
echo "=========================================="
echo "NEUROS v3.1 DEPLOYMENT COMPLETE!"
echo "=========================================="
echo "Features enabled:"
echo "- Biometric event triggers via Kafka"
echo "- 3 neuroplastic protocol stacks"
echo "- Dynamic mode switching based on HRV/sleep/stress"
echo "- Two-tier memory (Redis L1 + checkpoint L2)"
echo "- Pattern synthesis and hypothesis generation"
echo ""
echo "Note: ChromaDB removed due to infrastructure constraints"
echo "Using MemorySaver for L2 instead of PostgreSQL checkpointer"
EOF

echo "Deployment script complete!" 