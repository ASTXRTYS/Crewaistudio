#!/bin/bash
# =============================================================================
# AUREN Section 12 Deployment - LangGraph Production Runtime (Remote Workspace)
# =============================================================================
# Purpose: Deploy Section 12 with LangGraph patterns from remote workspace
# Target: Production server (144.126.215.218)
# =============================================================================

set -e  # Exit on error

# Configuration
SERVER_IP="144.126.215.218"
SERVER_USER="root"
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

# Step 1: Prepare deployment files locally
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

# Create deployment script for the server
cat > "$TEMP_DIR/deploy_on_server.sh" << 'DEPLOY_SCRIPT'
#!/bin/bash
set -e

DEPLOY_PATH="/opt/auren_deploy/section_12_langgraph"
BACKUP_PATH="/opt/auren_deploy/backups/$(date +%Y%m%d_%H%M%S)"

# Create backup
if [ -d /opt/auren_deploy/biometric-bridge ]; then
    mkdir -p $BACKUP_PATH
    cp -r /opt/auren_deploy/biometric-bridge/* $BACKUP_PATH/ 2>/dev/null || true
    echo "Backup created at $BACKUP_PATH"
fi

# Stop old service
cd /opt/auren_deploy/biometric-bridge
docker-compose down || true

# Build new image
cd $DEPLOY_PATH
docker build -t auren-section12-langgraph:latest .

# Update Prometheus if exists
if [ -f /opt/monitoring/prometheus/prometheus.yml ]; then
    if ! grep -q 'auren_section12_langgraph' /opt/monitoring/prometheus/prometheus.yml; then
        sed -i '/targets:/a\        - auren_section12_langgraph:8000' /opt/monitoring/prometheus/prometheus.yml
    fi
    docker exec prometheus kill -HUP 1 || true
fi

# Start new service
docker-compose up -d

# Wait and check health
sleep 10
curl -s http://localhost:8888/health | python3 -m json.tool

echo "Deployment complete!"
echo "API Key: $(grep AUREN_MASTER_API_KEY .env | cut -d= -f2)"
echo "LangGraph Key: $(grep LANGGRAPH_AES_KEY .env | cut -d= -f2)"
DEPLOY_SCRIPT

chmod +x "$TEMP_DIR/deploy_on_server.sh"

# Step 2: Create tar archive
echo -e "${YELLOW}📦 Creating deployment archive...${NC}"
cd "$TEMP_DIR"
tar czf /tmp/section12_langgraph.tar.gz .
cd -

echo -e "${GREEN}✅ Deployment package ready${NC}"
echo ""
echo -e "${YELLOW}📤 Please transfer the deployment package to the server:${NC}"
echo ""
echo "1. Copy the deployment package:"
echo "   scp /tmp/section12_langgraph.tar.gz root@$SERVER_IP:/tmp/"
echo ""
echo "2. SSH to the server and extract:"
echo "   ssh root@$SERVER_IP"
echo "   mkdir -p $DEPLOY_PATH"
echo "   cd $DEPLOY_PATH"
echo "   tar xzf /tmp/section12_langgraph.tar.gz"
echo "   ./deploy_on_server.sh"
echo ""
echo "Deployment package location: /tmp/section12_langgraph.tar.gz"
echo "Keys generated:"
echo "  - API Key: $AUREN_KEY"
echo "  - LangGraph Key: $LANGGRAPH_KEY"

# Cleanup temp dir
rm -rf "$TEMP_DIR"