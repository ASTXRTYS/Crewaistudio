#!/bin/bash

echo "🚀 Deploying NEUROS Advanced Reasoning..."

# Stop existing NEUROS container
echo "Stopping existing NEUROS container..."
docker stop neuros-langgraph || true
docker rm neuros-langgraph || true

# Build new image
echo "Building NEUROS Advanced image..."
cd /opt/auren_deploy/auren/agents/neuros
docker build -f Dockerfile.advanced -t neuros-advanced:latest .

# Run new container
echo "Starting NEUROS Advanced container..."
docker run -d \
  --name neuros-advanced \
  --network auren-network \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e PYTHONUNBUFFERED=1 \
  --restart unless-stopped \
  neuros-advanced:latest

# Wait for startup
echo "Waiting for NEUROS to start..."
sleep 10

# Check health
echo "Checking NEUROS health..."
curl -s http://localhost:8000/health || echo "Health check endpoint not available yet"

# Check logs
echo "Recent logs:"
docker logs --tail 20 neuros-advanced

echo "✅ NEUROS Advanced Reasoning deployment complete!"
echo "Access at: http://144.126.215.218:8000" 