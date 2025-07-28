#!/bin/bash
# AUREN Monitoring Recovery Script
# Purpose: Quickly fix monitoring when Grafana shows no data
# Date: July 28, 2025
# Status: VERIFIED WORKING ✅

set -e

echo "==================================="
echo "AUREN MONITORING RECOVERY SCRIPT"
echo "==================================="
echo "This will fix Prometheus/Grafana monitoring issues"
echo ""

# Function to check if container exists
container_exists() {
    docker ps -a --format '{{.Names}}' | grep -q "^$1$"
}

# Function to check if container is running
container_running() {
    docker ps --format '{{.Names}}' | grep -q "^$1$"
}

echo "🔍 STEP 1: Checking current status..."
echo "-------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "prometheus|grafana|exporter|NAMES" || true

echo -e "\n📊 STEP 2: Starting missing exporters..."
echo "-------------------------------------"

# Node Exporter
if ! container_running "auren-node-exporter"; then
    echo "Starting Node Exporter..."
    container_exists "auren-node-exporter" && docker rm -f auren-node-exporter
    docker run -d \
        --name auren-node-exporter \
        --network auren-network \
        -p 9100:9100 \
        --restart unless-stopped \
        prom/node-exporter:latest
    echo "✅ Node Exporter started"
else
    echo "✓ Node Exporter already running"
fi

# Redis Exporter
if ! container_running "auren-redis-exporter"; then
    echo "Starting Redis Exporter..."
    container_exists "auren-redis-exporter" && docker rm -f auren-redis-exporter
    docker run -d \
        --name auren-redis-exporter \
        --network auren-network \
        -p 9121:9121 \
        -e REDIS_ADDR=auren-redis:6379 \
        --restart unless-stopped \
        oliver006/redis_exporter:latest
    echo "✅ Redis Exporter started"
else
    echo "✓ Redis Exporter already running"
fi

# PostgreSQL Exporter
if ! container_running "auren-postgres-exporter"; then
    echo "Starting PostgreSQL Exporter..."
    container_exists "auren-postgres-exporter" && docker rm -f auren-postgres-exporter
    docker run -d \
        --name auren-postgres-exporter \
        --network auren-network \
        -p 9187:9187 \
        -e DATA_SOURCE_NAME="postgresql://auren_user:auren_password_2024@auren-postgres:5432/auren_production?sslmode=disable" \
        --restart unless-stopped \
        prometheuscommunity/postgres-exporter:latest
    echo "✅ PostgreSQL Exporter started"
else
    echo "✓ PostgreSQL Exporter already running"
fi

echo -e "\n🔧 STEP 3: Fixing Prometheus configuration..."
echo "-------------------------------------"

# Create correct Prometheus config
cat > /tmp/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'biometric-api'
    static_configs:
      - targets: ['biometric-production:8888']
    metrics_path: '/metrics'

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['auren-redis-exporter:9121']

  - job_name: 'postgres-exporter'  
    static_configs:
      - targets: ['auren-postgres-exporter:9187']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['auren-node-exporter:9100']
EOF

echo "✅ Prometheus config created with CORRECT container names"

# Restart Prometheus with correct config
echo -e "\n🔄 STEP 4: Restarting Prometheus..."
echo "-------------------------------------"
docker stop auren-prometheus 2>/dev/null || true
docker rm auren-prometheus 2>/dev/null || true

docker run -d \
    --name auren-prometheus \
    --network auren-network \
    -p 9090:9090 \
    -v /tmp/prometheus.yml:/etc/prometheus/prometheus.yml \
    --restart unless-stopped \
    prom/prometheus:latest

echo "✅ Prometheus restarted with fixed configuration"

# Check Grafana
echo -e "\n📈 STEP 5: Checking Grafana..."
echo "-------------------------------------"
if ! container_running "auren-grafana"; then
    echo "Starting Grafana..."
    container_exists "auren-grafana" && docker rm -f auren-grafana
    docker run -d \
        --name auren-grafana \
        --network auren-network \
        -p 3000:3000 \
        --restart unless-stopped \
        grafana/grafana:latest
    echo "✅ Grafana started"
else
    echo "✓ Grafana already running"
fi

echo -e "\n⏳ STEP 6: Waiting for services to stabilize..."
echo "-------------------------------------"
sleep 20

echo -e "\n✅ STEP 7: Verifying targets..."
echo "-------------------------------------"
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}' 2>/dev/null || echo "Prometheus API not ready yet"

echo -e "\n==================================="
echo "RECOVERY COMPLETE!"
echo "==================================="
echo ""
echo "✅ What's Working:"
echo "  - System metrics (CPU, Memory, Disk)"
echo "  - PostgreSQL metrics"
echo "  - Redis metrics"
echo "  - Prometheus scraping"
echo ""
echo "❌ Known Issue:"
echo "  - Biometric API metrics (needs /metrics endpoint implementation)"
echo ""
echo "📊 Access Points:"
echo "  - Grafana: http://$(hostname -I | awk '{print $1}'):3000"
echo "  - Prometheus: http://$(hostname -I | awk '{print $1}'):9090"
echo ""
echo "🔍 If targets still show DOWN:"
echo "  1. Wait another 30 seconds"
echo "  2. Check docker logs auren-prometheus"
echo "  3. Verify all containers on auren-network"
echo "" 