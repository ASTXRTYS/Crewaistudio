#!/bin/bash

echo "🚀 Deploying AUREN Dashboard Enhancements"
echo "========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${BLUE}Enhancements to deploy:${NC}"
echo "✅ Glassmorphism design system"
echo "✅ Particle background animations"
echo "✅ Biometric time-series visualizations"
echo "✅ Enhanced WebSocket with heartbeat"
echo "✅ Mobile-responsive layouts"
echo ""

# Step 1: Build the enhanced dashboard
echo -e "\n${YELLOW}Step 1: Building enhanced dashboard...${NC}"
cd auren/dashboard_v2

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build production version
echo "Building production bundle..."
npm run build

# Step 2: Copy new CSS files
echo -e "\n${YELLOW}Step 2: Copying enhanced styles...${NC}"
cp src/styles/glassmorphism.css dist/assets/

# Step 3: Create deployment package
echo -e "\n${YELLOW}Step 3: Creating deployment package...${NC}"
cd ../..
tar -czf dashboard-enhanced.tar.gz \
    auren/dashboard_v2/dist/ \
    auren/dashboard_v2/src/components/ParticleBackground.jsx \
    auren/dashboard_v2/src/components/BiometricChart.jsx \
    auren/dashboard_v2/src/components/EnhancedDashboard.jsx \
    auren/dashboard_v2/src/hooks/useEnhancedWebSocket.js \
    auren/dashboard_v2/src/styles/glassmorphism.css

# Step 4: Deploy to server
echo -e "\n${YELLOW}Step 4: Deploying to aupex.ai...${NC}"
echo "You'll be prompted for the server password..."

# Copy to server
scp dashboard-enhanced.tar.gz root@144.126.215.218:/tmp/

# Deploy on server
ssh root@144.126.215.218 << 'EOF'
echo "Deploying enhanced dashboard on server..."
cd /root/auren-production

# Backup current dashboard
echo "Creating backup..."
cp -r auren/dashboard_v2/dist auren/dashboard_v2/dist.backup.$(date +%Y%m%d_%H%M%S)

# Extract new files
echo "Extracting enhanced dashboard..."
tar -xzf /tmp/dashboard-enhanced.tar.gz

# Update nginx to ensure proper headers for glassmorphism
echo "Updating nginx configuration for enhanced features..."
cat > nginx-enhanced.conf << 'NGINX'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Enhanced security headers for glassmorphism
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Cache control for better performance
    map $sent_http_content_type $expires {
        default                    off;
        text/html                  epoch;
        text/css                   max;
        application/javascript     max;
        ~image/                    max;
        ~font/                     max;
    }

    server {
        listen 80;
        server_name aupex.ai www.aupex.ai;
        
        # Enable gzip for better performance
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

        # Dashboard with enhanced features
        root /usr/share/nginx/html;
        index index.html;
        
        location / {
            try_files $uri $uri/ /index.html;
            expires $expires;
            
            # Headers for WebGL and Canvas
            add_header Cross-Origin-Embedder-Policy "require-corp" always;
            add_header Cross-Origin-Opener-Policy "same-origin" always;
        }
        
        # API proxy
        location /api/ {
            proxy_pass http://auren-api:8080/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Enhanced WebSocket with heartbeat support
        location /ws {
            proxy_pass http://auren-api:8080/ws;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            
            # Increased timeouts for heartbeat
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
            proxy_connect_timeout 3600s;
        }
        
        # Health endpoint
        location /health {
            proxy_pass http://auren-api:8080/health;
            access_log off;
        }
    }
}
NGINX

# Update nginx configuration
mv nginx-enhanced.conf nginx.conf

# Restart services
echo "Restarting services..."
docker-compose -f docker-compose.prod.yml restart nginx auren-api

# Clean up
rm /tmp/dashboard-enhanced.tar.gz

echo "✅ Enhanced dashboard deployed successfully!"
echo ""
echo "New features available:"
echo "- Glassmorphism UI with frosted glass effects"
echo "- Neural particle background animations"
echo "- Biometric time-series visualizations"
echo "- Enhanced WebSocket with heartbeat and reconnection"
echo "- Mobile-responsive design"
echo ""
echo "Visit https://aupex.ai to see the enhancements!"
EOF

# Clean up local file
rm dashboard-enhanced.tar.gz

echo -e "\n${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Enhanced features now live at aupex.ai:"
echo "• Glassmorphism design system"
echo "• Particle backgrounds"
echo "• Biometric charts"
echo "• Real-time WebSocket enhancements"
echo "• Mobile responsiveness"
echo ""
echo "The dashboard now matches the expert-level standards from the training guide! 🎉" 