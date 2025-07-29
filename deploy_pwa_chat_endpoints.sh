#!/bin/bash

# AUREN PWA Chat Endpoints Deployment
# Following established procedures from DEPLOYMENT_PROCEDURES.md

echo "🚀 Starting PWA Chat Endpoints deployment..."
echo "📋 Following established deployment procedures"

# Step 1: Create deployment package
echo "📦 Creating deployment package..."
tar -czf pwa-chat-update.tar.gz \
  auren/biometric/complete_biometric_system_production.py \
  auren/biometric/requirements.txt

# Step 2: Upload to server
echo "📤 Uploading to server..."
sshpass -p '.HvddX+@6dArsKd' scp -o StrictHostKeyChecking=no \
  pwa-chat-update.tar.gz root@144.126.215.218:/tmp/

# Step 3: Deploy with zero downtime (Rolling Update)
echo "🔄 Performing rolling update..."
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
echo "📍 Connected to production server"

# Extract update
cd /tmp
tar -xzf pwa-chat-update.tar.gz

# Backup current system
echo "💾 Creating backup..."
docker exec biometric-production cp /app/complete_biometric_system.py /app/complete_biometric_system.backup.$(date +%Y%m%d_%H%M%S).py

# Update the production file
echo "📝 Updating production file..."
docker cp auren/biometric/complete_biometric_system_production.py biometric-production:/app/complete_biometric_system.py
docker cp auren/biometric/requirements.txt biometric-production:/app/

# Install new dependencies in running container
echo "📦 Installing new dependencies..."
docker exec biometric-production pip install aiofiles==23.2.1

# Restart the service gracefully
echo "♻️ Restarting biometric service..."
docker restart biometric-production

# Wait for service to be healthy
echo "⏳ Waiting for service health..."
sleep 10

# Verify health
if docker exec biometric-production curl -s http://localhost:8888/health | grep -q "healthy"; then
    echo "✅ Service is healthy!"
else
    echo "❌ Service health check failed!"
    exit 1
fi

# Test new endpoints
echo "🧪 Testing new chat endpoints..."
if curl -s http://144.126.215.218:8888/api/agents/neuros/status | grep -q "NEUROS"; then
    echo "✅ New endpoints are working!"
else
    echo "❌ New endpoints test failed!"
    exit 1
fi

# Cleanup
rm /tmp/pwa-chat-update.tar.gz
rm -rf /tmp/auren

echo "🎉 Deployment complete!"
EOF

# Step 4: Cleanup local
rm pwa-chat-update.tar.gz

echo "✅ PWA Chat Endpoints deployed successfully!"
echo "📊 New endpoints available:"
echo "  - POST /api/chat/neuros"
echo "  - POST /api/chat/voice" 
echo "  - POST /api/chat/upload"
echo "  - GET  /api/chat/history/{session_id}"
echo "  - GET  /api/agents/neuros/status"
echo "  - WS   /ws/chat/{session_id}" 