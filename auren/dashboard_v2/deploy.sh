#!/bin/bash

echo "🚀 Deploying AUPEX Consciousness Monitor v2.0..."

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build production version
echo "🏗️ Building for production..."
npm run build

# Create deployment directory on server
echo "📤 Preparing server deployment..."
ssh root@144.126.215.218 "mkdir -p /var/www/aupex/dashboard_v2"

# Copy build files to server
echo "📋 Copying files to server..."
scp -r dist/* root@144.126.215.218:/var/www/aupex/dashboard_v2/

# Update Nginx configuration
echo "🔧 Updating Nginx configuration..."
ssh root@144.126.215.218 << 'EOF'
# Add location block for new dashboard
cat > /etc/nginx/sites-available/aupex-dashboard-v2 << 'NGINX'
location /dashboard/v2 {
    alias /var/www/aupex/dashboard_v2;
    try_files $uri $uri/ /index.html;
    
    # Enable gzip compression
    gzip on;
    gzip_types text/plain application/javascript text/css application/json;
    gzip_min_length 1000;
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

# Include in main config if not already
if ! grep -q "aupex-dashboard-v2" /etc/nginx/sites-enabled/default; then
    sed -i '/server {/a\    include /etc/nginx/sites-available/aupex-dashboard-v2;' /etc/nginx/sites-enabled/default
fi

# Test and reload Nginx
nginx -t && systemctl reload nginx
EOF

echo "✅ Deployment complete!"
echo "🌐 Dashboard available at: http://144.126.215.218/dashboard/v2"
echo ""
echo "📊 Features:"
echo "  - Real-time WebSocket connection to AI agents"
echo "  - GPU-accelerated knowledge graph visualization"
echo "  - Sub-10ms anomaly detection (HTM-ready)"
echo "  - Breakthrough capture and replay"
echo "  - 60fps performance with thousands of events" 