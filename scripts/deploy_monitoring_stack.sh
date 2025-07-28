#!/bin/bash
# Deploy Prometheus and Grafana monitoring stack to production

echo "🔍 Deploying Observability Stack (Prometheus + Grafana)"
echo "======================================================="

# First, create the prometheus config on the server
echo "📝 Creating Prometheus configuration..."
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
cat > /root/prometheus.yml << 'PROMETHEUS_CONFIG'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'redis'
    static_configs:
      - targets: ['auren-redis:6379']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['auren-postgres:5432']
    metrics_path: '/metrics'

  - job_name: 'biometric-api'
    static_configs:
      - targets: ['biometric-production:8888']
    metrics_path: '/health'

  - job_name: 'kafka'
    static_configs:
      - targets: ['auren-kafka:9092']
    metrics_path: '/metrics'

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
PROMETHEUS_CONFIG

echo "✅ Prometheus config created"
EOF

# Deploy Prometheus
echo "🚀 Deploying Prometheus..."
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
docker run -d \
  --name auren-prometheus \
  --network auren-network \
  -p 9090:9090 \
  -v /root/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v prometheus-data:/prometheus \
  --restart unless-stopped \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.console.libraries=/usr/share/prometheus/console_libraries \
  --web.console.templates=/usr/share/prometheus/consoles

echo "⏳ Waiting for Prometheus to start..."
sleep 10

# Check if Prometheus is running
if docker ps | grep -q auren-prometheus; then
    echo "✅ Prometheus is running"
    docker logs --tail 10 auren-prometheus
else
    echo "❌ Prometheus failed to start"
    docker logs auren-prometheus
fi
EOF

# Deploy Grafana
echo "🎨 Deploying Grafana..."
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
# Create Grafana provisioning directories
mkdir -p /root/grafana/provisioning/datasources
mkdir -p /root/grafana/provisioning/dashboards

# Create Prometheus datasource for Grafana
cat > /root/grafana/provisioning/datasources/prometheus.yml << 'DATASOURCE'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://auren-prometheus:9090
    isDefault: true
    editable: true
DATASOURCE

# Deploy Grafana
docker run -d \
  --name auren-grafana \
  --network auren-network \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=auren_grafana_2025 \
  -e GF_USERS_ALLOW_SIGN_UP=false \
  -e GF_SERVER_ROOT_URL=http://144.126.215.218:3000 \
  -v grafana-data:/var/lib/grafana \
  -v /root/grafana/provisioning:/etc/grafana/provisioning \
  --restart unless-stopped \
  grafana/grafana:latest

echo "⏳ Waiting for Grafana to start..."
sleep 15

# Check if Grafana is running
if docker ps | grep -q auren-grafana; then
    echo "✅ Grafana is running"
    docker logs --tail 10 auren-grafana
else
    echo "❌ Grafana failed to start"
    docker logs auren-grafana
fi
EOF

# Deploy exporters for better metrics
echo "📊 Deploying metric exporters..."
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
# Redis Exporter
docker run -d \
  --name auren-redis-exporter \
  --network auren-network \
  -p 9121:9121 \
  -e REDIS_ADDR=redis://auren-redis:6379 \
  --restart unless-stopped \
  oliver006/redis_exporter:latest

# PostgreSQL Exporter
docker run -d \
  --name auren-postgres-exporter \
  --network auren-network \
  -p 9187:9187 \
  -e DATA_SOURCE_NAME="postgresql://auren_user:auren_secure_2025@auren-postgres:5432/auren_production?sslmode=disable" \
  --restart unless-stopped \
  prometheuscommunity/postgres-exporter:latest

# Node Exporter for system metrics
docker run -d \
  --name auren-node-exporter \
  --network auren-network \
  -p 9100:9100 \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v /:/rootfs:ro \
  --restart unless-stopped \
  prom/node-exporter:latest \
  --path.procfs=/host/proc \
  --path.sysfs=/host/sys \
  --collector.filesystem.mount-points-exclude='^/(sys|proc|dev|host|etc)($$|/)'

echo "✅ Exporters deployed"
EOF

# Update firewall rules
echo "🔥 Updating firewall rules..."
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
# Open ports for monitoring
ufw allow 9090/tcp comment "Prometheus"
ufw allow 3000/tcp comment "Grafana"
ufw reload

echo "✅ Firewall rules updated"
EOF

# Final status check
echo -e "\n📊 MONITORING STACK DEPLOYMENT COMPLETE!\n"
echo "Access your observability tools at:"
echo "- Prometheus: http://144.126.215.218:9090"
echo "- Grafana: http://144.126.215.218:3000"
echo ""
echo "Grafana credentials:"
echo "- Username: admin"
echo "- Password: auren_grafana_2025"
echo ""
echo "⚡ Quick verification:"

# Test access
echo -e "\nTesting Prometheus..."
curl -s http://144.126.215.218:9090/-/healthy && echo "✅ Prometheus is accessible" || echo "❌ Prometheus not accessible"

echo -e "\nTesting Grafana..."
curl -s http://144.126.215.218:3000/api/health && echo "✅ Grafana is accessible" || echo "❌ Grafana not accessible"

echo -e "\n🎯 Next steps:"
echo "1. Access Grafana at http://144.126.215.218:3000"
echo "2. Login with admin/auren_grafana_2025"
echo "3. Create dashboards for:"
echo "   - System metrics (CPU, Memory, Disk)"
echo "   - PostgreSQL performance"
echo "   - Redis cache statistics"
echo "   - Biometric API response times"
echo "   - Kafka message throughput" 