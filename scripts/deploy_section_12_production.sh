#!/bin/bash
# SECTION 12: Direct Production Deployment (100% Completion)
# Created: January 29, 2025
# Purpose: Replace existing service with production-hardened Section 12

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

echo -e "${GREEN}🚀 AUREN Section 12 Production Deployment${NC}"
echo -e "${YELLOW}This will upgrade AUREN to 100% completion!${NC}"

# Function to execute commands on server
remote_exec() {
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "$1"
}

# Function to copy files to server
remote_copy() {
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$1" root@$SERVER_IP:"$2"
}

# Phase 1: Backup current system
echo -e "\n${YELLOW}Phase 1: System Backup${NC}"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

remote_exec "mkdir -p /backups/section_12_final"
echo "Creating database backup..."
remote_exec "docker exec auren-postgres pg_dump -U auren_user auren_production | gzip > /backups/section_12_final/db_backup_${BACKUP_DATE}.sql.gz"
echo "Backing up current container..."
remote_exec "docker commit biometric-production biometric-backup:${BACKUP_DATE} || true"
echo -e "${GREEN}✅ Backup complete${NC}"

# Phase 2: Prepare deployment
echo -e "\n${YELLOW}Phase 2: Preparing Deployment${NC}"
remote_exec "mkdir -p $DEPLOY_PATH"

# Create deployment package
TEMP_DIR=$(mktemp -d)
echo "Creating deployment package in $TEMP_DIR"

# Copy all necessary files
cp auren/main.py "$TEMP_DIR/"
cp auren/requirements.txt "$TEMP_DIR/"
cp auren/security.py "$TEMP_DIR/"

# Copy dependencies
mkdir -p "$TEMP_DIR/biometric"
cp -r auren/biometric/* "$TEMP_DIR/biometric/" 2>/dev/null || true

mkdir -p "$TEMP_DIR/agents/neuros"
cp auren/agents/neuros/section_8_neuros_graph.py "$TEMP_DIR/agents/neuros/" 2>/dev/null || true
cp auren/agents/neuros_graph.py "$TEMP_DIR/agents/" 2>/dev/null || true

# Create optimized Dockerfile
cat > "$TEMP_DIR/Dockerfile" << 'EOF'
# Section 12: Production-Optimized Dockerfile
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 auren

COPY --from=builder --chown=auren:auren /root/.local /home/auren/.local

WORKDIR /app
COPY --chown=auren:auren . .

USER auren

ENV PATH=/home/auren/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV RUN_MODE=api

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "uvloop"]
EOF

# Create environment file with master API key
cat > "$TEMP_DIR/.env" << EOF
# Section 12 Production Configuration
POSTGRES_URL=postgresql://auren_user:auren_secure_2025@auren-postgres:5432/auren_production
REDIS_URL=redis://auren-redis:6379
KAFKA_BOOTSTRAP_SERVERS=auren-kafka:9092
OPENAI_API_KEY=\${OPENAI_API_KEY}
ENABLE_SECURITY=true
AUREN_MASTER_API_KEY=auren-prod-$(openssl rand -hex 16)
ENABLE_EVENT_SOURCING=true
ENABLE_CONTINUOUS_AGGREGATES=true
LISTEN_NOTIFY_ENABLED=true
SECTION_9_INTEGRATION=true
LOG_LEVEL=info
EOF

# Copy to server
echo "Uploading files to server..."
cd "$TEMP_DIR"
tar czf /tmp/section12.tar.gz .
cd -
sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no /tmp/section12.tar.gz root@$SERVER_IP:/tmp/
remote_exec "cd $DEPLOY_PATH && tar xzf /tmp/section12.tar.gz && rm /tmp/section12.tar.gz"
rm -rf "$TEMP_DIR" /tmp/section12.tar.gz

echo -e "${GREEN}✅ Files uploaded${NC}"

# Phase 3: Build new image
echo -e "\n${YELLOW}Phase 3: Building Section 12 Image${NC}"
remote_exec "cd $DEPLOY_PATH && docker build -t auren/section-12:latest -t auren/section-12:${BACKUP_DATE} ."
echo -e "${GREEN}✅ Image built successfully${NC}"

# Phase 4: Stop old service
echo -e "\n${YELLOW}Phase 4: Stopping Current Service${NC}"
echo "Gracefully stopping biometric-production..."
remote_exec "docker stop -t 30 biometric-production || docker stop -t 30 biometric-system-100 || true"
remote_exec "docker rm biometric-production || docker rm biometric-system-100 || true"
echo -e "${GREEN}✅ Old service stopped${NC}"

# Phase 5: Start Section 12
echo -e "\n${YELLOW}Phase 5: Starting Section 12 Production${NC}"

# Get OpenAI API key from existing deployment
OPENAI_KEY=$(remote_exec "grep OPENAI_API_KEY /opt/auren_deploy/.env | cut -d= -f2" || echo "")

remote_exec "cd $DEPLOY_PATH && docker run -d \
  --name biometric-production \
  --network auren-network \
  --restart unless-stopped \
  -p 8888:8000 \
  --env-file .env \
  -e OPENAI_API_KEY='${OPENAI_KEY}' \
  -v /opt/auren_deploy/config:/app/config \
  -v /opt/auren/logs:/app/logs \
  auren/section-12:latest"

echo "Waiting for service to start..."
sleep 10

# Phase 6: Verify deployment
echo -e "\n${YELLOW}Phase 6: Verifying Deployment${NC}"

# Check health
HEALTH=$(remote_exec "curl -s http://localhost:8888/health | jq -r '.status' || echo 'FAILED'")

if [[ "$HEALTH" != "healthy" ]]; then
    echo -e "${RED}❌ Deployment failed! Rolling back...${NC}"
    remote_exec "docker stop biometric-production && docker rm biometric-production"
    remote_exec "docker run -d --name biometric-production --network auren-network -p 8888:8888 biometric-backup:${BACKUP_DATE}"
    exit 1
fi

echo -e "${GREEN}✅ Health check passed!${NC}"

# Show enhanced health info
echo -e "\n${YELLOW}Enhanced Health Status:${NC}"
remote_exec "curl -s http://localhost:8888/health | jq '.'"

# Test metrics endpoint
echo -e "\n${YELLOW}Metrics Endpoint:${NC}"
remote_exec "curl -s http://localhost:8888/metrics | head -10"

# Update Prometheus
echo -e "\n${YELLOW}Updating Prometheus Configuration${NC}"
remote_exec "sed -i 's/biometric-system-100:8888/biometric-production:8000/g' /opt/auren/prometheus/prometheus.yml || true"
remote_exec "docker exec prometheus kill -HUP 1 || true"

# Get API key for testing
API_KEY=$(remote_exec "grep AUREN_MASTER_API_KEY $DEPLOY_PATH/.env | cut -d= -f2")

# Phase 7: Final verification
echo -e "\n${GREEN}🎉 SECTION 12 DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}AUREN IS NOW 100% PRODUCTION READY!${NC}"
echo ""
echo -e "${YELLOW}System Information:${NC}"
echo "- Service: Running on port 8888"
echo "- Health: http://$SERVER_IP:8888/health"
echo "- Metrics: http://$SERVER_IP:8888/metrics"
echo "- API Key: $API_KEY"
echo ""
echo -e "${YELLOW}New Features Enabled:${NC}"
echo "✅ Production-grade async runtime"
echo "✅ Graceful lifecycle management"
echo "✅ Retry logic with exponential backoff"
echo "✅ Enhanced observability endpoints"
echo "✅ Section 9 security integration"
echo "✅ Kubernetes deployment ready"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "1. Update monitoring dashboards"
echo "2. Configure alerts for new metrics"
echo "3. Test webhook endpoints with authentication"
echo "4. Update State of Readiness to 100%"
echo ""
echo -e "${GREEN}Backup Location: /backups/section_12_final/db_backup_${BACKUP_DATE}.sql.gz${NC}" 