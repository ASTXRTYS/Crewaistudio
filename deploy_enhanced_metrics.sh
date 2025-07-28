#!/bin/bash
# Deploy enhanced metrics to AUREN biometric API

set -e

echo "🚀 Deploying Enhanced Metrics to AUREN"

# Server details
SERVER="144.126.215.218"
PASSWORD=".HvddX+@6dArsKd"

# Step 1: Copy files to server
echo "📦 Copying enhanced metrics files..."
sshpass -p "$PASSWORD" scp enhanced_api_metrics.py root@$SERVER:/tmp/
sshpass -p "$PASSWORD" scp deploy_enhanced_metrics.py root@$SERVER:/tmp/

# Step 2: Copy original file from container for enhancement
echo "📋 Getting current biometric system file..."
sshpass -p "$PASSWORD" ssh root@$SERVER << 'EOF'
# Copy current file from container
docker cp biometric-production:/app/complete_biometric_system.py /tmp/complete_biometric_system.py

# Run the enhancement script
cd /tmp
python3 deploy_enhanced_metrics.py

# Check if enhanced file was created
if [ -f "complete_biometric_system_enhanced.py" ]; then
    echo "✅ Enhanced file created successfully"
else
    echo "❌ Failed to create enhanced file"
    exit 1
fi
EOF

# Step 3: Deploy enhanced files to container
echo "🔧 Deploying enhanced files to container..."
sshpass -p "$PASSWORD" ssh root@$SERVER << 'EOF'
# Copy enhanced metrics module
docker cp /tmp/enhanced_api_metrics.py biometric-production:/app/

# Copy enhanced main file
docker cp /tmp/complete_biometric_system_enhanced.py biometric-production:/app/complete_biometric_system.py

# Install Enum from prometheus_client if needed
docker exec biometric-production pip install --upgrade prometheus-client
EOF

# Step 4: Restart container
echo "🔄 Restarting biometric container..."
sshpass -p "$PASSWORD" ssh root@$SERVER << 'EOF'
docker restart biometric-production

# Wait for startup
echo "⏳ Waiting for container to start..."
sleep 15

# Check if container is healthy
if docker ps | grep -q "biometric-production.*healthy"; then
    echo "✅ Container is healthy"
else
    echo "⚠️  Container may not be healthy, checking logs..."
    docker logs --tail 20 biometric-production
fi
EOF

# Step 5: Verify metrics
echo "🔍 Verifying enhanced metrics..."
sshpass -p "$PASSWORD" ssh root@$SERVER << 'EOF'
# Test metrics endpoint
echo "Testing metrics endpoint..."
METRICS=$(curl -s http://localhost:8888/metrics)

# Check for our custom metrics
if echo "$METRICS" | grep -q "auren_webhook_requests_total"; then
    echo "✅ Webhook metrics found"
else
    echo "❌ Webhook metrics NOT found"
fi

if echo "$METRICS" | grep -q "auren_memory_tier_operations_total"; then
    echo "✅ Memory tier metrics found"
else
    echo "❌ Memory tier metrics NOT found"
fi

if echo "$METRICS" | grep -q "auren_neuros_mode_switches_total"; then
    echo "✅ NEUROS mode metrics found"
else
    echo "❌ NEUROS mode metrics NOT found"
fi

if echo "$METRICS" | grep -q "auren_biometric_events_processed_total"; then
    echo "✅ Biometric event metrics found"
else
    echo "❌ Biometric event metrics NOT found"
fi

# Count total custom metrics
CUSTOM_METRICS=$(echo "$METRICS" | grep -c "^auren_" || true)
echo "📊 Total custom AUREN metrics: $CUSTOM_METRICS"
EOF

echo "✅ Enhanced metrics deployment complete!"
echo ""
echo "📊 Next steps:"
echo "1. Create enhanced Grafana dashboards"
echo "2. Send test webhooks to generate metrics"
echo "3. Monitor at http://144.126.215.218:3000" 