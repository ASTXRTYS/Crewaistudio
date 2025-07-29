#!/bin/bash

echo "🚀 Deploying NEUROS Website Updates"
echo "===================================="

# Navigate to correct directory
cd /Users/Jason/Downloads/CrewAI-Studio-main

# Package the website from correct location
echo "📦 Creating deployment package..."
cd AUPEX_WEBSITE_DOCUMENTATION/02_Implementation
tar -czf ../../neuros-website-update.tar.gz .

cd ../..

# Use sshpass for deployment
echo "📤 Uploading to server..."
sshpass -p '.HvddX+@6dArsKd' scp neuros-website-update.tar.gz root@144.126.215.218:/tmp/

echo "🔧 Deploying on server..."
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
# Backup current website
echo "Creating backup..."
cd /var/www
tar -czf html-backup-$(date +%Y%m%d-%H%M%S).tar.gz html/

# Extract new website
echo "Extracting new files..."
cd /var/www/html
tar -xzf /tmp/neuros-website-update.tar.gz

# Restart nginx to ensure changes take effect
echo "Restarting nginx..."
systemctl restart nginx

# Cleanup
rm /tmp/neuros-website-update.tar.gz

echo "✅ NEUROS website updates deployed!"
EOF

# Cleanup local file
rm neuros-website-update.tar.gz

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "Visit the updated pages:"
echo "- Home: http://aupex.ai/"
echo "- NEUROS Dashboard: http://aupex.ai/agents/neuros.html"
echo "- Agents Listing: http://aupex.ai/agents/"
echo ""
echo "Changes deployed:"
echo "- NEUROS branding (formerly Neuroscientist)"
echo "- Black Steel and Space theme"
echo "- Core Specializations section" 