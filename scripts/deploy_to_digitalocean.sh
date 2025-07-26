#!/bin/bash

# AUREN DigitalOcean Deployment Script
# This moves all services from local to your droplet

DROPLET_IP="144.126.215.218"
SSH_USER="root"

echo "🚀 AUREN DigitalOcean Deployment"
echo "================================"

# Step 1: Stop local services to free up resources
echo "1. Stopping local Docker services..."
read -p "Stop all local Docker containers? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose down
    echo "✅ Local services stopped"
fi

# Step 2: Package the application
echo -e "\n2. Packaging application..."
tar -czf auren-deploy.tar.gz \
    docker-compose.yml \
    docker-compose.prod.yml \
    Dockerfile.api \
    auren/ \
    scripts/ \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='node_modules'

# Step 3: Copy to droplet
echo -e "\n3. Copying to DigitalOcean droplet..."
scp auren-deploy.tar.gz $SSH_USER@$DROPLET_IP:/root/

# Step 4: Deploy on droplet
echo -e "\n4. Deploying on droplet..."
ssh $SSH_USER@$DROPLET_IP << 'EOF'
    # Extract files
    cd /root
    mkdir -p auren-deployment
    tar -xzf auren-deploy.tar.gz -C auren-deployment/
    cd auren-deployment
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
    fi
    
    # Install docker-compose if not present
    if ! command -v docker-compose &> /dev/null; then
        curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    
    # Start services
    docker-compose -f docker-compose.yml up -d
    
    echo "✅ Services deployed!"
EOF

# Step 5: Configure firewall
echo -e "\n5. Configuring firewall..."
ssh $SSH_USER@$DROPLET_IP << 'EOF'
    # Open necessary ports
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    ufw allow 8080/tcp  # API
    ufw allow 8081/tcp  # Kafka UI
    ufw allow 3000/tcp  # Grafana
    ufw --force enable
EOF

echo -e "\n✅ Deployment complete!"
echo "Access your services at:"
echo "- API: http://$DROPLET_IP:8080"
echo "- Kafka UI: http://$DROPLET_IP:8081"
echo "- Grafana: http://$DROPLET_IP:3000"

# Cleanup
rm -f auren-deploy.tar.gz 