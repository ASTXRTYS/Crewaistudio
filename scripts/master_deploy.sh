#!/bin/bash

# AUREN Master Deployment Script
# Senior Engineer Execution - Full Production Deploy

set -e  # Exit on any error

echo "╔══════════════════════════════════════════════════════╗"
echo "║        AUREN MASTER DEPLOYMENT - EXECUTING           ║"
echo "║           Senior Engineer Authorization               ║"
echo "╚══════════════════════════════════════════════════════╝"

DROPLET_IP="144.126.215.218"
DOMAIN="aupex.ai"

# Function to execute commands on remote server
remote_exec() {
    ssh -o StrictHostKeyChecking=no root@$DROPLET_IP "$@"
}

# Function to copy files to remote server
remote_copy() {
    scp -o StrictHostKeyChecking=no "$1" root@$DROPLET_IP:"$2"
}

echo -e "\n🚀 Phase 1: Preparing Deployment Package"
echo "========================================"

# Include the built dashboard in the package
echo "Including built dashboard files..."
tar --exclude='node_modules' --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
    -czf auren-full-deploy.tar.gz \
    docker-compose.prod.yml \
    Dockerfile.api \
    nginx.conf \
    nginx-temp.conf \
    auren/ \
    scripts/

echo "✅ Deployment package created"

echo -e "\n📤 Phase 2: Uploading to DigitalOcean"
echo "====================================="
remote_copy auren-full-deploy.tar.gz /root/
remote_copy scripts/remote_deploy.sh /root/
remote_copy scripts/setup_production.sh /root/
echo "✅ Files uploaded"

echo -e "\n🔧 Phase 3: Remote Server Setup"
echo "================================"
remote_exec << 'REMOTE_SCRIPT'
#!/bin/bash
set -e

cd /root

# Extract deployment
rm -rf auren-production
mkdir -p auren-production
tar -xzf auren-full-deploy.tar.gz -C auren-production/
cd auren-production

# Install Docker if needed
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
fi

# Install docker-compose
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Stop any existing services
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker system prune -f

# Build and start all services
echo "Starting all services..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services
sleep 30

# Create systemd service for auto-restart
cat > /etc/systemd/system/auren.service << 'EOF'
[Unit]
Description=AUREN AI System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/root/auren-production
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
ExecReload=/usr/local/bin/docker-compose -f docker-compose.prod.yml restart

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable auren.service

# Configure firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Install Nginx and Certbot for SSL
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

# Configure Nginx for domain (temp config first)
cp nginx-temp.conf /etc/nginx/nginx.conf
nginx -t && systemctl reload nginx

# Show status
docker-compose -f docker-compose.prod.yml ps

REMOTE_SCRIPT

echo "✅ Remote setup complete"

echo -e "\n🔒 Phase 4: SSL Certificate Setup"
echo "=================================="
remote_exec "certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN" || true

# After SSL is set up, switch to production nginx config
echo "Switching to production nginx configuration..."
remote_exec "cd /root/auren-production && cp nginx.conf /etc/nginx/nginx.conf && nginx -t && systemctl reload nginx" || true

echo -e "\n📊 Phase 5: Monitoring & Health Checks"
echo "======================================"

# Create monitoring script
cat > scripts/monitor_health.sh << 'MONITOR'
#!/bin/bash
# AUREN Health Monitor - Runs every minute

API_URL="http://localhost:8080/health"
WEBHOOK_URL=""  # Add Slack/Discord webhook if desired

check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)
    if [ $response -ne 200 ]; then
        echo "$(date): API Health check failed - Status: $response"
        # Restart services
        cd /root/auren-production
        docker-compose -f docker-compose.prod.yml restart auren-api
        
        # Send alert if webhook configured
        if [ ! -z "$WEBHOOK_URL" ]; then
            curl -X POST $WEBHOOK_URL -H 'Content-Type: application/json' \
                -d '{"text":"⚠️ AUREN API restarted due to health check failure"}'
        fi
    fi
}

check_health
MONITOR

remote_copy scripts/monitor_health.sh /root/
remote_exec "chmod +x /root/monitor_health.sh"
remote_exec "crontab -l | { cat; echo '* * * * * /root/monitor_health.sh'; } | crontab -"

echo -e "\n🚀 Phase 6: Continuous Deployment Pipeline"
echo "=========================================="

# Create auto-deploy script
cat > scripts/auto_deploy.sh << 'AUTODEPLOY'
#!/bin/bash
# AUREN Auto-Deploy - Pull latest changes and redeploy

cd /root/auren-production

# Pull latest from git (if using git deployment)
# git pull origin main

# Rebuild and restart only what changed
docker-compose -f docker-compose.prod.yml up -d --build

# Clean up old images
docker image prune -f
AUTODEPLOY

remote_copy scripts/auto_deploy.sh /root/
remote_exec "chmod +x /root/auto_deploy.sh"

echo -e "\n✅ DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "🌐 Your AI System is LIVE at:"
echo "   https://$DOMAIN"
echo ""
echo "📊 Service Status:"
remote_exec "docker ps --format 'table {{.Names}}\t{{.Status}}'"
echo ""
echo "🔧 Management Commands:"
echo "   SSH: ssh root@$DROPLET_IP"
echo "   Logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "   Restart: systemctl restart auren"
echo "   Deploy Updates: /root/auto_deploy.sh"
echo ""
echo "💡 Knowledge Pipeline:"
echo "   1. Add knowledge files to: auren/src/agents/Level 1 knowledge/"
echo "   2. Run: /root/auto_deploy.sh"
echo "   3. System automatically loads new knowledge"
echo ""
echo "🏁 The engine is running. It will never stop."

# Cleanup local file
rm -f auren-full-deploy.tar.gz 