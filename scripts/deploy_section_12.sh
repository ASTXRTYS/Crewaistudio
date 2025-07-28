#!/bin/bash
# SECTION 12: Production Runtime Deployment Script
# Created: January 29, 2025
# Purpose: Deploy production-hardened main execution layer

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SERVER_IP="144.126.215.218"
SERVER_PASSWORD=".HvddX+@6dArsKd"
DEPLOY_PATH="/opt/auren_deploy/section_12"
PARALLEL_PORT="8889"  # For parallel testing
PRODUCTION_PORT="8888"  # Final deployment

echo -e "${GREEN}🚀 Starting Section 12 Deployment${NC}"
echo -e "${YELLOW}This will deploy the production runtime alongside existing services${NC}"

# Function to execute commands on server
remote_exec() {
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "$1"
}

# Function to copy files to server
remote_copy() {
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$1" root@$SERVER_IP:"$2"
}

# Phase 1: Pre-deployment checks
echo -e "\n${YELLOW}Phase 1: Pre-deployment Health Check${NC}"
echo "Checking current system status..."

HEALTH_CHECK=$(remote_exec "curl -s http://localhost:8888/health || echo 'FAILED'")
if [[ "$HEALTH_CHECK" == "FAILED" ]]; then
    echo -e "${RED}❌ Current biometric service is not healthy!${NC}"
    echo "Please fix the existing service before deploying Section 12"
    exit 1
fi

echo -e "${GREEN}✅ Current service is healthy${NC}"

# Phase 2: Backup current configuration
echo -e "\n${YELLOW}Phase 2: Backing Up Current Configuration${NC}"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

remote_exec "mkdir -p /backups/section_12_deployment"
remote_exec "docker exec auren-postgres pg_dump -U auren_user auren_production | gzip > /backups/section_12_deployment/db_backup_${BACKUP_DATE}.sql.gz"
echo -e "${GREEN}✅ Database backed up${NC}"

# Phase 3: Prepare deployment directory
echo -e "\n${YELLOW}Phase 3: Preparing Deployment Directory${NC}"
remote_exec "mkdir -p $DEPLOY_PATH/{scripts,config}"

# Phase 4: Copy files
echo -e "\n${YELLOW}Phase 4: Copying Section 12 Files${NC}"

# Create temporary directory for staging
TEMP_DIR=$(mktemp -d)
echo "Staging files in $TEMP_DIR"

# Copy main application
cp auren/main.py "$TEMP_DIR/"
cp auren/requirements.txt "$TEMP_DIR/"

# Copy necessary dependencies
mkdir -p "$TEMP_DIR/biometric"
cp -r auren/biometric/* "$TEMP_DIR/biometric/" 2>/dev/null || true

mkdir -p "$TEMP_DIR/agents"
cp -r auren/agents/neuros_graph.py "$TEMP_DIR/agents/" 2>/dev/null || true

# Create Dockerfile
cat > "$TEMP_DIR/Dockerfile" << 'EOF'
# Section 12: Production Dockerfile
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user early
RUN useradd -m -u 1000 auren

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 auren

# Copy installed packages from builder
COPY --from=builder --chown=auren:auren /root/.local /home/auren/.local

# Set up app directory
WORKDIR /app
COPY --chown=auren:auren . .

# Switch to non-root user
USER auren

# Add local bin to PATH
ENV PATH=/home/auren/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default to API mode
ENV RUN_MODE=api

# Expose API port
EXPOSE 8000

# Health check with proper endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use consistent startup method
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create docker-compose for Section 12
cat > "$TEMP_DIR/docker-compose.section12.yml" << 'EOF'
version: '3.8'

services:
  biometric-section-12:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: biometric-section-12
    restart: unless-stopped
    networks:
      - auren-network
    ports:
      - "8889:8000"
    environment:
      RUN_MODE: api
      POSTGRES_URL: postgresql://auren_user:auren_secure_2025@auren-postgres:5432/auren_production
      REDIS_URL: redis://auren-redis:6379
      KAFKA_BOOTSTRAP_SERVERS: auren-kafka:9092
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      API_PORT: 8000
      LOG_LEVEL: info
      ENABLE_EVENT_SOURCING: "true"
      ENABLE_CONTINUOUS_AGGREGATES: "true"
      LISTEN_NOTIFY_ENABLED: "true"
      SECTION_9_INTEGRATION: "true"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

networks:
  auren-network:
    external: true
EOF

# Copy all files to server
echo "Copying files to server..."
remote_copy "$TEMP_DIR/*" "$DEPLOY_PATH/"

# Clean up temp directory
rm -rf "$TEMP_DIR"

echo -e "${GREEN}✅ Files copied successfully${NC}"

# Phase 5: Build and deploy
echo -e "\n${YELLOW}Phase 5: Building and Deploying Section 12${NC}"

# Copy environment file
remote_exec "cp /opt/auren_deploy/.env $DEPLOY_PATH/.env"

# Build image
echo "Building Docker image..."
remote_exec "cd $DEPLOY_PATH && docker-compose -f docker-compose.section12.yml build"

# Start service
echo "Starting Section 12 service on port $PARALLEL_PORT..."
remote_exec "cd $DEPLOY_PATH && docker-compose -f docker-compose.section12.yml up -d"

# Wait for service to be ready
echo "Waiting for service to be ready..."
sleep 10

# Phase 6: Validate deployment
echo -e "\n${YELLOW}Phase 6: Validating Deployment${NC}"

# Check health endpoint
SECTION_12_HEALTH=$(remote_exec "curl -s http://localhost:$PARALLEL_PORT/health | jq -r '.status' || echo 'FAILED'")

if [[ "$SECTION_12_HEALTH" != "healthy" ]]; then
    echo -e "${RED}❌ Section 12 deployment failed!${NC}"
    echo "Rolling back..."
    remote_exec "cd $DEPLOY_PATH && docker-compose -f docker-compose.section12.yml down"
    exit 1
fi

echo -e "${GREEN}✅ Section 12 is healthy!${NC}"

# Show comparison
echo -e "\n${YELLOW}Service Comparison:${NC}"
echo "Old Service (port 8888):"
remote_exec "curl -s http://localhost:8888/health | jq '.components' || echo 'Basic health check'"

echo -e "\nNew Service (port $PARALLEL_PORT):"
remote_exec "curl -s http://localhost:$PARALLEL_PORT/health | jq '.'"

# Phase 7: Performance test
echo -e "\n${YELLOW}Phase 7: Performance Testing${NC}"
echo "Running basic load test..."

# Install ab if not present
remote_exec "which ab || apt-get update && apt-get install -y apache2-utils"

echo "Testing old service:"
remote_exec "ab -n 100 -c 10 -t 5 http://localhost:8888/health | grep 'Requests per second'"

echo "Testing new service:"
remote_exec "ab -n 100 -c 10 -t 5 http://localhost:$PARALLEL_PORT/health | grep 'Requests per second'"

# Phase 8: Monitoring setup
echo -e "\n${YELLOW}Phase 8: Configuring Monitoring${NC}"

# Update Prometheus configuration
remote_exec "cat >> /opt/auren/prometheus/prometheus.yml << 'EOF'

  - job_name: 'section-12'
    static_configs:
      - targets: ['biometric-section-12:8000']
        labels:
          service: 'section-12'
          environment: 'production'
EOF"

# Reload Prometheus
remote_exec "docker exec prometheus kill -HUP 1 || true"

echo -e "${GREEN}✅ Monitoring configured${NC}"

# Summary
echo -e "\n${GREEN}🎉 Section 12 Deployment Complete!${NC}"
echo -e "${YELLOW}Service Status:${NC}"
echo "- Current service: Running on port 8888"
echo "- Section 12: Running on port $PARALLEL_PORT"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Monitor both services for 24 hours"
echo "2. Compare metrics and performance"
echo "3. Run cutover script when ready: ./scripts/cutover_section_12.sh"
echo ""
echo -e "${YELLOW}Testing Commands:${NC}"
echo "- Health: curl http://$SERVER_IP:$PARALLEL_PORT/health"
echo "- Metrics: curl http://$SERVER_IP:$PARALLEL_PORT/metrics"
echo "- Webhook test: curl -X POST http://$SERVER_IP:$PARALLEL_PORT/webhooks/test -d '{}'"
echo ""
echo -e "${GREEN}Remember to update documentation after successful validation!${NC}" 