#!/bin/bash

echo "Deploying dashboard to aupex.ai..."

# First, create the deployment package locally
echo "Creating deployment package..."
tar -czf dashboard-deploy.tar.gz \
  auren/dashboard_v2/src/ \
  auren/dashboard_v2/package.json \
  auren/dashboard_v2/vite.config.js \
  auren/dashboard_v2/index.html

# Use expect to automate the deployment
expect << 'EOF'
set timeout 300
spawn ssh root@144.126.215.218

expect "password:"
send ".HvddX+@6dArsKd\r"

expect "# "
send "cd /root/auren-production\r"

expect "# "
send "# First, let's check what's running\r"
send "docker-compose -f docker-compose.prod.yml ps\r"

expect "# "
send "# Stop the nginx container that's blocking port 80\r"
send "docker stop auren-nginx || true\r"

expect "# "
send "# Remove it to free the port\r"
send "docker rm auren-nginx || true\r"

expect "# "
send "# Also check for any other process on port 80\r"
send "lsof -i :80 | grep LISTEN || true\r"

expect "# "
send "# Kill any remaining processes on port 80\r"
send "fuser -k 80/tcp || true\r"

expect "# "
send "# Now update the dashboard code\r"
send "cd /root\r"

expect "# "
send "exit\r"
EOF

# Now copy our deployment package
echo "Copying files to server..."
expect << 'EOF'
spawn scp dashboard-deploy.tar.gz root@144.126.215.218:/tmp/
expect "password:"
send ".HvddX+@6dArsKd\r"
expect eof
EOF

# Deploy on server
echo "Deploying on server..."
expect << 'EOF'
set timeout 600
spawn ssh root@144.126.215.218

expect "password:"
send ".HvddX+@6dArsKd\r"

expect "# "
send "cd /root/auren-production\r"

expect "# "
send "# Extract the new dashboard files\r"
send "tar -xzf /tmp/dashboard-deploy.tar.gz\r"

expect "# "
send "# Rebuild the dashboard\r"
send "cd auren/dashboard_v2\r"

expect "# "
send "npm install\r"

expect "# "
send "npm run build\r"

expect "# "
send "cd /root/auren-production\r"

expect "# "
send "# Now restart all services\r"
send "docker-compose -f docker-compose.prod.yml down\r"

expect "# "
send "docker-compose -f docker-compose.prod.yml up -d --build\r"

expect "# "
send "# Check if everything is running\r"
send "sleep 10\r"

expect "# "
send "docker-compose -f docker-compose.prod.yml ps\r"

expect "# "
send "# Clean up\r"
send "rm /tmp/dashboard-deploy.tar.gz\r"

expect "# "
send "echo 'Deployment complete!'\r"

expect "# "
send "exit\r"
EOF

# Clean up local file
rm dashboard-deploy.tar.gz

echo "Deployment finished! Check aupex.ai in a few moments." 