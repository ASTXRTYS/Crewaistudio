#!/bin/bash

echo "Simple dashboard deployment to aupex.ai..."

# Build locally first
echo "Building dashboard locally..."
cd auren/dashboard_v2
npm run build
cd ../..

# Create tarball of just the built files
echo "Creating deployment package..."
tar -czf dashboard-dist.tar.gz -C auren/dashboard_v2 dist/

# Deploy using expect
expect << 'EOF'
set timeout 300

# Copy the built files
spawn scp dashboard-dist.tar.gz root@144.126.215.218:/tmp/
expect "password:"
send ".HvddX+@6dArsKd\r"
expect eof

# Now deploy on server
spawn ssh root@144.126.215.218
expect "password:"
send ".HvddX+@6dArsKd\r"

expect "# "
send "cd /root/auren-production\r"

expect "# "
send "# Check current nginx status\r"
send "docker ps | grep nginx || true\r"

expect "# "
send "# Stop any existing nginx\r"
send "docker stop \$(docker ps -q --filter name=nginx) || true\r"

expect "# "
send "# Extract new dashboard files\r"
send "mkdir -p auren/dashboard_v2/dist\r"

expect "# "
send "rm -rf auren/dashboard_v2/dist/*\r"

expect "# "
send "tar -xzf /tmp/dashboard-dist.tar.gz -C auren/dashboard_v2/\r"

expect "# "
send "# Check if nginx config exists\r"
send "ls -la nginx.conf\r"

expect "# "
send "# Restart services\r"
send "docker-compose -f docker-compose.prod.yml down\r"

expect "# "
send "docker-compose -f docker-compose.prod.yml up -d\r"

expect "# "
send "# Wait for services to start\r"
send "sleep 15\r"

expect "# "
send "# Check status\r"
send "docker-compose -f docker-compose.prod.yml ps\r"

expect "# "
send "# Clean up\r"
send "rm /tmp/dashboard-dist.tar.gz\r"

expect "# "
send "echo 'Dashboard deployed!'\r"

expect "# "
send "exit\r"
EOF

# Clean up
rm dashboard-dist.tar.gz

echo "Deployment complete! Check aupex.ai now." 