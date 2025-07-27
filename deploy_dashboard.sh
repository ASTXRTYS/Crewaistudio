#!/bin/bash

echo "Deploying dashboard updates to aupex.ai..."

# Build the dashboard
echo "Building dashboard..."
cd auren/dashboard_v2
npm run build
cd ../..

# Create a tarball of the built files
echo "Creating deployment package..."
tar -czf dashboard-update.tar.gz -C auren/dashboard_v2 dist/

# Copy to server
echo "Uploading to server..."
echo "You'll be prompted for the server password..."
scp dashboard-update.tar.gz root@144.126.215.218:/tmp/

# Deploy on server
echo "Deploying on server..."
ssh root@144.126.215.218 << 'EOF'
cd /root/auren-production
# Extract new dashboard files
tar -xzf /tmp/dashboard-update.tar.gz -C auren/dashboard_v2/
# Restart services
docker-compose -f docker-compose.prod.yml restart auren-api nginx
# Clean up
rm /tmp/dashboard-update.tar.gz
echo "Dashboard deployed successfully!"
EOF

# Clean up local file
rm dashboard-update.tar.gz

echo "Deployment complete! Check aupex.ai in a few moments." 