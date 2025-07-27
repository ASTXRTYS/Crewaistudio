#!/bin/bash

echo "🔧 Quick Fix for AUREN Dashboard"
echo "================================"

SERVER_IP="144.126.215.218"

echo "Restarting services on server..."
ssh root@$SERVER_IP << 'EOF'
cd /root/auren-production

echo "1. Restarting Docker services..."
docker-compose -f docker-compose.prod.yml restart nginx auren-api

echo "2. Waiting for services to start..."
sleep 5

echo "3. Checking service status..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "nginx|auren-api"

echo "4. Testing endpoints..."
curl -s http://localhost/api/health | jq . || echo "API not ready yet"

echo "5. Checking nginx error logs..."
docker logs auren-nginx --tail=10 2>&1 | grep -i error || echo "No errors found"

echo "Done! Services restarted."
EOF

echo ""
echo "✅ Services restarted. Try accessing http://aupex.ai now!"
echo "If still not loading, try:"
echo "1. Clear browser cache (Ctrl+Shift+R)"
echo "2. Try incognito/private mode"
echo "3. Check browser console for errors (F12)" 