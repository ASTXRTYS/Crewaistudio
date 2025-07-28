#!/bin/bash
# Fix Prometheus metrics instrumentation in biometric API

echo "🔧 Adding Prometheus instrumentation to biometric API..."

# Create the metrics module
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
cd /app

# Create a proper metrics module
cat > metrics.py << 'METRICS_CODE'
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Define metrics
webhook_requests = Counter(
    'biometric_webhook_requests_total',
    'Total webhook requests received',
    ['device_type', 'status']
)

event_processing_time = Histogram(
    'biometric_event_processing_seconds',
    'Time spent processing biometric events',
    ['event_type']
)

active_connections = Gauge(
    'biometric_active_connections',
    'Number of active connections'
)

kafka_messages_sent = Counter(
    'biometric_kafka_messages_sent_total',
    'Total messages sent to Kafka',
    ['topic']
)

database_operations = Counter(
    'biometric_database_operations_total',
    'Total database operations',
    ['operation', 'table']
)

memory_tier_access = Counter(
    'memory_tier_access_total',
    'Memory tier access counts',
    ['tier', 'operation']
)

# Health metrics
system_health = Gauge(
    'biometric_system_health',
    'Overall system health (1=healthy, 0=unhealthy)'
)
system_health.set(1)  # Default to healthy

def get_metrics():
    """Generate Prometheus metrics"""
    return generate_latest()
METRICS_CODE

# Update the biometric API to use real metrics
cd /app/auren/biometric
cp api.py api.py.backup

# Add imports and update metrics endpoint
cat > update_metrics.py << 'UPDATE_SCRIPT'
import re

# Read the original file
with open('api.py', 'r') as f:
    content = f.read()

# Add metrics import after other imports
import_line = "from app.metrics import get_metrics, webhook_requests, event_processing_time, kafka_messages_sent, database_operations"
content = content.replace(
    "from typing import Dict, Any, Optional, List",
    f"from typing import Dict, Any, Optional, List\n{import_line}"
)

# Replace the metrics endpoint
old_metrics = '''@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    # Note: In production, use prometheus_client.generate_latest()
    return {
        "status": "metrics",
        "message": "Prometheus metrics endpoint",
        "info": "Configure prometheus_client to expose metrics here"
    }'''

new_metrics = '''@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from fastapi import Response
    from prometheus_client import CONTENT_TYPE_LATEST
    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)'''

content = content.replace(old_metrics, new_metrics)

# Add metric instrumentation to webhook endpoints
# Find webhook handler pattern and add metrics
webhook_pattern = r'(@app\.post\("/webhooks/(\w+)"\)[\s\S]*?async def \w+\(.*?\):)'
def add_webhook_metrics(match):
    device = match.group(2)
    original = match.group(0)
    return original + f'\n    webhook_requests.labels(device_type="{device}", status="received").inc()'

content = re.sub(webhook_pattern, add_webhook_metrics, content)

# Write the updated file
with open('api.py', 'w') as f:
    f.write(content)

print("✅ API updated with Prometheus metrics")
UPDATE_SCRIPT

python3 update_metrics.py

# Copy metrics module to container
docker cp metrics.py biometric-production:/app/
docker cp api.py biometric-production:/app/auren/biometric/

# Restart the biometric container to load changes
docker restart biometric-production

echo "⏳ Waiting for container to restart..."
sleep 10

# Verify metrics endpoint is now working
echo "Testing metrics endpoint..."
curl -s http://localhost:8888/metrics | head -20

echo "✅ Prometheus metrics instrumentation complete!"
EOF

# Update Prometheus configuration to fix the scrape configs
echo "🔧 Fixing Prometheus scrape configurations..."
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
# Update prometheus config with correct targets
cat > /root/prometheus.yml << 'PROMETHEUS_CONFIG'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'biometric-api'
    static_configs:
      - targets: ['144.126.215.218:8888']
    metrics_path: '/metrics'

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['144.126.215.218:9121']

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['144.126.215.218:9187']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['144.126.215.218:9100']
PROMETHEUS_CONFIG

# Restart Prometheus with new config
docker restart auren-prometheus

echo "✅ Prometheus configuration updated!"
EOF

echo "🎯 Prometheus metrics fix complete!"
echo ""
echo "Verify at:"
echo "- Metrics endpoint: http://144.126.215.218:8888/metrics"
echo "- Prometheus targets: http://144.126.215.218:9090/targets" 