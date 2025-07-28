#!/bin/bash
# Fix Prometheus metrics instrumentation in biometric API - v2

echo "🔧 Adding Prometheus instrumentation to biometric API..."

# First, let's find where the biometric API actually is
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
echo "Finding biometric API location..."
docker exec biometric-production find / -name "api.py" -type f 2>/dev/null | grep biometric | head -5
EOF

# Create metrics module locally first
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

# Copy metrics module to server
sshpass -p '.HvddX+@6dArsKd' scp metrics.py root@144.126.215.218:/tmp/

# Now work inside the container
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
# Copy metrics module into container
docker cp /tmp/metrics.py biometric-production:/app/

# Install prometheus_client if not already installed
docker exec biometric-production pip install prometheus-client

# Update the API inside the container
docker exec biometric-production bash -c 'cd /app && cat > fix_metrics.py << "SCRIPT"
import re
import os

# Find the api.py file
api_paths = [
    "/app/api.py",
    "/app/auren/biometric/api.py",
    "/app/biometric/api.py"
]

api_file = None
for path in api_paths:
    if os.path.exists(path):
        api_file = path
        print(f"Found API at: {path}")
        break

if not api_file:
    print("ERROR: Could not find api.py")
    exit(1)

# Read the file
with open(api_file, "r") as f:
    content = f.read()

# Check if metrics import already exists
if "from app.metrics import" not in content:
    # Add import after other imports
    import_line = "from app.metrics import get_metrics, webhook_requests, event_processing_time, kafka_messages_sent, database_operations"
    
    # Find a good place to add the import
    if "from typing import" in content:
        content = content.replace(
            "from typing import Dict, Any, Optional, List",
            f"from typing import Dict, Any, Optional, List\n{import_line}"
        )
    else:
        # Add after the first import
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                lines.insert(i + 1, import_line)
                break
        content = "\n".join(lines)

# Update the metrics endpoint
old_patterns = [
    r"@app\.get\(\"/metrics\"\)[\s\S]*?return\s*{[\s\S]*?}",
    r"@app\.get\(\"/metrics\"\)[\s\S]*?async def metrics\(\):[\s\S]*?}[\s\S]*?}"
]

new_metrics = """@app.get("/metrics")
async def metrics():
    \"\"\"Prometheus metrics endpoint\"\"\"
    from fastapi import Response
    from prometheus_client import CONTENT_TYPE_LATEST
    try:
        metrics_data = get_metrics()
        return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        # Fallback if metrics module not found
        return {"error": str(e), "status": "metrics module not loaded"}"""

# Try each pattern
replaced = False
for pattern in old_patterns:
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_metrics, content, flags=re.DOTALL)
        replaced = True
        print(f"Replaced metrics endpoint using pattern: {pattern[:30]}...")
        break

if not replaced:
    print("WARNING: Could not find metrics endpoint to replace")

# Save the updated file
with open(api_file, "w") as f:
    f.write(content)

print(f"✅ Updated {api_file}")
SCRIPT
'

# Run the fix script
docker exec biometric-production python /app/fix_metrics.py

# Restart the container
docker restart biometric-production

echo "⏳ Waiting for container to restart..."
sleep 15

# Test the metrics endpoint
echo "Testing metrics endpoint..."
curl -s http://localhost:8888/metrics | head -10
EOF

# Update Prometheus configuration
echo "🔧 Updating Prometheus configuration..."
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
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

docker restart auren-prometheus
EOF

echo "✅ Prometheus fix complete!"
echo ""
echo "Check status at:"
echo "- http://144.126.215.218:9090/targets"
echo "- http://144.126.215.218:8888/metrics"

# Clean up
rm -f metrics.py 