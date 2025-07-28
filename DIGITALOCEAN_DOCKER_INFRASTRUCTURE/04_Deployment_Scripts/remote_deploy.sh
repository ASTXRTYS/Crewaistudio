#!/bin/bash

# AUREN Remote Deployment Script
# Run this on your DigitalOcean server after copying files

echo "🚀 AUREN DigitalOcean Deployment Starting..."
echo "=========================================="

# Extract deployment package
cd /root
echo "1. Extracting files..."
rm -rf auren-deployment
mkdir -p auren-deployment
tar -xzf auren-deploy.tar.gz -C auren-deployment/
cd auren-deployment

# Install Docker if needed
if ! command -v docker &> /dev/null; then
    echo "2. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
else
    echo "2. Docker already installed ✓"
fi

# Install docker-compose if needed
if ! command -v docker-compose &> /dev/null; then
    echo "3. Installing docker-compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "3. Docker-compose already installed ✓"
fi

# Stop any existing services
echo "4. Stopping any existing services..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# Build and start all services
echo "5. Starting all services..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
echo "6. Waiting for services to start..."
sleep 30

# Check service status
echo "7. Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# Configure firewall
echo "8. Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8080/tcp  # API (temporary, will be proxied)
ufw allow 8081/tcp  # Kafka UI (optional)
ufw allow 3000/tcp  # Grafana (optional)
ufw --force enable

# Set up domain (if not already done)
echo "9. Domain Configuration"
echo "Make sure your DNS A record points to: 144.126.215.218"
echo "Domain: aupex.ai"

# Display access information
echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "🌐 Access your services:"
echo "- Website: http://aupex.ai (or http://144.126.215.218)"
echo "- API Health: http://144.126.215.218:8080/health"
echo "- Kafka UI: http://144.126.215.218:8081 (if enabled)"
echo ""
echo "📊 Service Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔧 Next Steps:"
echo "1. Set up SSL certificate with Let's Encrypt:"
echo "   certbot --nginx -d aupex.ai -d www.aupex.ai"
echo "2. Monitor logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f"
echo "" 