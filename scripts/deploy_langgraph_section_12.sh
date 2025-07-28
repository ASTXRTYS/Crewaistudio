#!/bin/bash
# =============================================================================
# AUREN Section 12 Deployment - LangGraph Production Runtime
# =============================================================================
# Purpose: Deploy Section 12 with LangGraph patterns (no CrewAI)
# Target: Production server (144.126.215.218)
# =============================================================================

set -e  # Exit on error

# Configuration
SERVER_IP="144.126.215.218"
SERVER_USER="root"
SERVER_PASSWORD='.HvddX+@6dArsKd'
DEPLOY_PATH="/opt/auren_deploy/section_12_langgraph"
BACKUP_PATH="/opt/auren_deploy/backups/$(date +%Y%m%d_%H%M%S)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 AUREN Section 12 LangGraph Deployment${NC}"
echo "=========================================="
echo "Target: $SERVER_IP"
echo "Deploy Path: $DEPLOY_PATH"
echo ""

# Helper functions
remote_exec() {
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$1"
}

remote_copy() {
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$1" "$SERVER_USER@$SERVER_IP:$2"
}

# Step 1: Create backup of current deployment
echo -e "${YELLOW}📦 Creating backup of current deployment...${NC}"
remote_exec "
if [ -d /opt/auren_deploy/biometric-bridge ]; then
    mkdir -p $BACKUP_PATH
    cp -r /opt/auren_deploy/biometric-bridge/* $BACKUP_PATH/ 2>/dev/null || true
    echo 'Backup created at $BACKUP_PATH'
fi
"

# Step 2: Prepare deployment files
echo -e "${YELLOW}📝 Preparing deployment files...${NC}"
TEMP_DIR=$(mktemp -d)

# Copy necessary files
cp auren/main_langgraph.py "$TEMP_DIR/main.py"
cp auren/security.py "$TEMP_DIR/security.py"
cp auren/requirements_langgraph.txt "$TEMP_DIR/requirements.txt"

# Create Dockerfile
cat > "$TEMP_DIR/Dockerfile" << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create non-root user
RUN useradd -m -u 1000 auren && chown -R auren:auren /app
USER auren

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create docker-compose.yml
cat > "$TEMP_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  auren-section12:
    build: .
    image: auren-section12-langgraph:latest
    container_name: auren_section12_langgraph
    restart: unless-stopped
    ports:
      - "8888:8000"
    environment:
      - POSTGRES_URL=postgresql://auren_user:auren_secure_2025@postgres:5432/auren_production
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AUREN_MASTER_API_KEY=${AUREN_MASTER_API_KEY}
      - ENABLE_SECURITY=true
      - API_PORT=8000
      - LANGGRAPH_AES_KEY=${LANGGRAPH_AES_KEY}
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
      - RUN_MODE=api
    networks:
      - auren-network
    depends_on:
      - postgres
      - redis
    volumes:
      - /var/log/auren:/app/logs

networks:
  auren-network:
    external: true
EOF

# Create environment file
AUREN_KEY=$(openssl rand -hex 32)
LANGGRAPH_KEY=$(openssl rand -hex 32)
cat > "$TEMP_DIR/.env" << EOF
OPENAI_API_KEY=your_openai_key_here
AUREN_MASTER_API_KEY=$AUREN_KEY
LANGGRAPH_AES_KEY=$LANGGRAPH_KEY
LANGSMITH_API_KEY=your_langsmith_key_here
EOF

# Step 3: Upload files to server
echo -e "${YELLOW}📤 Uploading files to server...${NC}"
remote_exec "mkdir -p $DEPLOY_PATH"

# Create tar archive for transfer
cd "$TEMP_DIR"
tar czf /tmp/section12_langgraph.tar.gz .
cd -

# Transfer and extract
remote_copy "/tmp/section12_langgraph.tar.gz" "/tmp/"
remote_exec "cd $DEPLOY_PATH && tar xzf /tmp/section12_langgraph.tar.gz && rm /tmp/section12_langgraph.tar.gz"

# Cleanup
rm -rf "$TEMP_DIR" /tmp/section12_langgraph.tar.gz

echo -e "${GREEN}✅ Files uploaded${NC}"

# Step 4: Stop old service
echo -e "${YELLOW}🛑 Stopping old service...${NC}"
remote_exec "
cd /opt/auren_deploy/biometric-bridge
docker-compose down || true
"

# Step 5: Build new image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
remote_exec "
cd $DEPLOY_PATH
docker build -t auren-section12-langgraph:latest .
"

# Step 6: Update Prometheus configuration
echo -e "${YELLOW}📊 Updating Prometheus configuration...${NC}"
remote_exec "
if [ -f /opt/monitoring/prometheus/prometheus.yml ]; then
    # Add new target if not exists
    if ! grep -q 'auren_section12_langgraph' /opt/monitoring/prometheus/prometheus.yml; then
        sed -i '/targets:/a\        - auren_section12_langgraph:8000' /opt/monitoring/prometheus/prometheus.yml
    fi
    # Reload Prometheus
    docker exec prometheus kill -HUP 1 || true
fi
"

# Step 7: Start new service
echo -e "${YELLOW}🚀 Starting Section 12 LangGraph service...${NC}"
remote_exec "
cd $DEPLOY_PATH
docker-compose up -d
"

# Step 8: Wait for service to be ready
echo -e "${YELLOW}⏳ Waiting for service to be ready...${NC}"
sleep 10

# Step 9: Health check
echo -e "${YELLOW}🏥 Running health check...${NC}"
HEALTH_CHECK=$(remote_exec "curl -s http://localhost:8888/health" || echo "FAILED")

if echo "$HEALTH_CHECK" | grep -q "langgraph"; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
    echo "$HEALTH_CHECK" | python3 -m json.tool
else
    echo -e "${RED}❌ Health check failed!${NC}"
    echo "Response: $HEALTH_CHECK"
    
    # Show logs
    echo -e "${YELLOW}📋 Recent logs:${NC}"
    remote_exec "cd $DEPLOY_PATH && docker-compose logs --tail=50"
    
    exit 1
fi

# Step 10: Create migration documentation
echo -e "${YELLOW}📝 Creating migration documentation...${NC}"
remote_exec "cat > $DEPLOY_PATH/MIGRATION_NOTES.md << 'EOF'
# Section 12 LangGraph Migration
Date: $(date)

## What Changed
- Migrated from CrewAI to LangGraph patterns
- Implemented proper state management with reducers
- Added PostgreSQL checkpointing
- Integrated LangSmith observability
- Enhanced biometric event routing

## Key Features
1. Device-specific processing (Oura, WHOOP, Apple Health)
2. Parallel event processing with proper state merging
3. Memory tier management (hot/warm/cold)
4. Streaming analysis results
5. Production-grade error handling

## Configuration
- Main service: Port 8888
- Metrics: /metrics (Prometheus format)
- Health: /health
- Readiness: /readiness

## Rollback Instructions
If needed, restore from backup:
\`\`\`bash
cd /opt/auren_deploy
docker-compose -f biometric-bridge/docker-compose.yml down
cp -r $BACKUP_PATH/* biometric-bridge/
docker-compose -f biometric-bridge/docker-compose.yml up -d
\`\`\`

## API Keys
- AUREN Master Key: $AUREN_KEY
- LangGraph AES Key: $LANGGRAPH_KEY
EOF"

# Step 11: Update nginx (if applicable)
echo -e "${YELLOW}🌐 Checking nginx configuration...${NC}"
remote_exec "
if [ -f /etc/nginx/sites-available/auren ]; then
    echo 'Nginx configuration found - no changes needed (still using port 8888)'
fi
"

# Step 12: Final summary
echo -e "${GREEN}
=============================================================================
✅ SECTION 12 LANGGRAPH DEPLOYMENT COMPLETE!
=============================================================================

🔗 Service URL: http://$SERVER_IP:8888
📊 Metrics: http://$SERVER_IP:8888/metrics
🏥 Health: http://$SERVER_IP:8888/health
📚 Docs: http://$SERVER_IP:8888/docs

🔑 API Key: $AUREN_KEY
🔐 LangGraph Key: $LANGGRAPH_KEY

📁 Deployment Path: $DEPLOY_PATH
📦 Backup Path: $BACKUP_PATH

✨ Key Improvements:
- No CrewAI dependencies
- LangGraph state management with reducers
- PostgreSQL checkpointing for persistence
- Streaming analysis results
- Production-grade observability

⚡ Next Steps:
1. Update OPENAI_API_KEY in $DEPLOY_PATH/.env
2. Configure LANGSMITH_API_KEY for observability
3. Test webhook endpoints with real biometric data
4. Monitor logs: docker logs -f auren_section12_langgraph

${NC}"

echo -e "${YELLOW}📋 To view logs:${NC}"
echo "sshpass -p '$SERVER_PASSWORD' ssh root@$SERVER_IP 'docker logs -f auren_section12_langgraph'"