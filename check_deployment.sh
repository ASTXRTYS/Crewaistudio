#!/bin/bash

echo "🔍 Checking AUREN Deployment Status"
echo "===================================="

SERVER_IP="144.126.215.218"
PASSWORD=".HvddX+@6dArsKd"

# Create expect script for SSH
cat > check_deploy.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 30
set password [lindex $argv 0]

spawn ssh root@144.126.215.218 << 'ENDSSH'
echo "1. Checking dashboard files..."
ls -la /root/auren-production/auren/dashboard_v2/dist/ | head -10

echo -e "\n2. Checking for glassmorphism CSS..."
if [ -f /root/auren-production/auren/dashboard_v2/src/styles/glassmorphism.css ]; then
    echo "✅ glassmorphism.css exists"
else
    echo "❌ glassmorphism.css NOT FOUND"
fi

echo -e "\n3. Checking nginx served content..."
curl -s http://localhost | grep -c "glass" || echo "No glass styles found"

echo -e "\n4. Checking Docker services..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "nginx|auren-api"

echo -e "\n5. Checking nginx config..."
grep -E "location|proxy_pass" /root/auren-production/nginx.conf | head -10

echo -e "\n6. Checking if deployment is in progress..."
ps aux | grep -E "tar|scp|cp" | grep -v grep || echo "No active deployment processes"
ENDSSH

expect {
    "password:" {
        send "$password\r"
        exp_continue
    }
    eof
}
EOF

chmod +x check_deploy.exp
./check_deploy.exp "$PASSWORD"
rm check_deploy.exp

echo -e "\n✅ Check complete!" 