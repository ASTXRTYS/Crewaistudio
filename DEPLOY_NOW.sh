#!/bin/bash
# IMMEDIATE DEPLOYMENT SCRIPT - Deploy Sections 1-8 to DigitalOcean NOW

set -e  # Exit on error

echo "🚀 DEPLOYING BIOMETRIC BRIDGE + NEUROS TO PRODUCTION..."

# Server details
SERVER_IP="144.126.215.218"
SERVER_USER="root"

# Step 1: Create deployment package
echo "📦 Creating deployment package..."
mkdir -p deploy_package
cp -r auren/biometric/* deploy_package/
cp -r auren/agents/neuros deploy_package/
cp -r config/agents/neuros_agent_profile.yaml deploy_package/

# Create production Dockerfile
cat > deploy_package/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y gcc g++ postgresql-client curl && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] \
    langgraph langchain langchain-openai \
    aiokafka confluent-kafka \
    asyncpg psycopg2-binary \
    redis[hiredis] \
    pyyaml python-dotenv \
    structlog prometheus-client

# Copy all code
COPY . /app/

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create unified service
RUN echo 'import os; os.system("cd /app && python -m uvicorn unified_service:app --host 0.0.0.0 --port 8000")' > start.py

EXPOSE 8000
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "start.py"]
EOF

# Create environment file
cat > deploy_package/.env << 'EOF'
POSTGRES_URL=postgresql://auren_user:securepwd123!@postgres:5432/auren_production
REDIS_URL=redis://redis:6379/0
KAFKA_BROKERS=kafka:9092
OPENAI_API_KEY=${OPENAI_API_KEY}
LOG_LEVEL=INFO
EOF

# Step 2: Copy to server
echo "📤 Copying files to server..."
scp -r deploy_package/* ${SERVER_USER}@${SERVER_IP}:/opt/auren/biometric-service/

# Step 3: Build and run on server
echo "🔨 Building and deploying on server..."
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /opt/auren/biometric-service

# Stop any existing service
docker stop biometric-unified || true
docker rm biometric-unified || true

# Build image
docker build -t auren/biometric-unified:latest .

# Run service
docker run -d \
  --name biometric-unified \
  --network auren_default \
  --restart unless-stopped \
  -p 8888:8000 \
  --env-file .env \
  auren/biometric-unified:latest

# Check if running
sleep 5
docker ps | grep biometric-unified
curl http://localhost:8888/health

echo "✅ DEPLOYMENT COMPLETE!"
echo "Service running at: http://144.126.215.218:8888"
ENDSSH

# Cleanup
rm -rf deploy_package

echo "🎉 BIOMETRIC BRIDGE + NEUROS DEPLOYED AND RUNNING!"
echo "Check status at: http://144.126.215.218:8888/health" 