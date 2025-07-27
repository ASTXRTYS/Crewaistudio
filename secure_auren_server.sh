#!/bin/bash

echo "=== AUREN Server Security Hardening Script ==="
echo "This will secure your DigitalOcean server at 144.126.215.218"
echo "============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${YELLOW}This script will:${NC}"
echo "1. Update docker-compose.prod.yml to bind services to localhost only"
echo "2. Configure UFW firewall properly"
echo "3. Set up SSL with Let's Encrypt"
echo "4. Harden SSH configuration"
echo "5. Install fail2ban"
echo "6. Set up automated security updates"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo -e "\n${GREEN}Step 1: Creating secure docker-compose file${NC}"
cat > docker-compose.prod.secure.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL - Bound to localhost only
  postgres:
    image: timescale/timescaledb:latest-pg16
    container_name: auren-postgres
    ports:
      - "127.0.0.1:5432:5432"  # Only accessible from localhost
    environment:
      POSTGRES_DB: auren_db
      POSTGRES_USER: auren_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-auren_password_2024}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init:/docker-entrypoint-initdb.d
      - ./auren/database/init_schema.sql:/docker-entrypoint-initdb.d/02_init_schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U auren_user -d auren_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    command: >
      postgres
      -c ssl=on
      -c ssl_cert_file=/var/lib/postgresql/server.crt
      -c ssl_key_file=/var/lib/postgresql/server.key
      -c log_statement=all
      -c log_connections=on
      -c log_disconnections=on

  # Redis - Bound to localhost only
  redis:
    image: redis:7-alpine
    container_name: auren-redis
    ports:
      - "127.0.0.1:6379:6379"  # Only accessible from localhost
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    command: redis-server --requirepass ${REDIS_PASSWORD:-auren_redis_2024}

  # ChromaDB - Bound to localhost only
  chromadb:
    image: chromadb/chroma:0.4.22
    container_name: auren-chromadb
    ports:
      - "127.0.0.1:8000:8000"  # Only accessible from localhost
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
      - CHROMA_SERVER_AUTH_PROVIDER=token
      - CHROMA_SERVER_AUTH_TOKEN=${CHROMA_TOKEN:-auren_chroma_2024}
    restart: unless-stopped

  # API Service - Bound to localhost only
  auren-api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: auren-api
    ports:
      - "127.0.0.1:8080:8080"  # Only accessible from localhost
    environment:
      - DATABASE_URL=postgresql://auren_user:${POSTGRES_PASSWORD:-auren_password_2024}@postgres:5432/auren_db
      - REDIS_URL=redis://:${REDIS_PASSWORD:-auren_redis_2024}@redis:6379
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8000
      - CHROMA_TOKEN=${CHROMA_TOKEN:-auren_chroma_2024}
      - JWT_SECRET=${JWT_SECRET:-your_jwt_secret_here}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY:-your_32_byte_encryption_key_here}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      chromadb:
        condition: service_started
    restart: unless-stopped
    volumes:
      - ./auren:/app/auren
      - ./src:/app/src

  # Nginx - Public facing
  nginx:
    image: nginx:alpine
    container_name: auren-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./auren/dashboard_v2/dist:/usr/share/nginx/html:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - auren-api
    restart: unless-stopped

  # Certbot for SSL
  certbot:
    image: certbot/certbot
    container_name: auren-certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

volumes:
  postgres_data:
  redis_data:
  chromadb_data:

networks:
  default:
    name: auren-network
EOF

echo -e "\n${GREEN}Step 2: Creating secure Nginx configuration${NC}"
cat > nginx.secure.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general:10m rate=50r/s;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name aupex.ai www.aupex.ai;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name aupex.ai www.aupex.ai;

        ssl_certificate /etc/letsencrypt/live/aupex.ai/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/aupex.ai/privkey.pem;

        # Frontend
        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
            limit_req zone=general burst=20 nodelay;
        }

        # API proxy with rate limiting
        location /api/ {
            proxy_pass http://auren-api:8080/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Rate limiting for API
            limit_req zone=api burst=20 nodelay;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # WebSocket with rate limiting
        location /ws {
            proxy_pass http://auren-api:8080/ws;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            
            # Rate limiting for WebSocket
            limit_req zone=api burst=10 nodelay;
        }

        # Health check endpoint (no rate limiting)
        location /health {
            proxy_pass http://auren-api:8080/health;
            access_log off;
        }
    }
}
EOF

echo -e "\n${GREEN}Step 3: Creating deployment script${NC}"
cat > deploy_secure.sh << 'DEPLOY_SCRIPT'
#!/bin/bash

SERVER_IP="144.126.215.218"
DOMAIN="aupex.ai"

echo "Deploying secure configuration to $SERVER_IP..."

# Copy files to server
scp docker-compose.prod.secure.yml nginx.secure.conf root@$SERVER_IP:/root/auren-production/

# Execute on server
ssh root@$SERVER_IP << 'EOF'
cd /root/auren-production

# Stop current services
docker-compose -f docker-compose.prod.yml down

# Backup current config
cp docker-compose.prod.yml docker-compose.prod.yml.backup
cp nginx.conf nginx.conf.backup

# Install security tools
apt-get update
apt-get install -y ufw fail2ban unattended-upgrades

# Configure UFW firewall
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable

# Configure fail2ban
cat > /etc/fail2ban/jail.local << 'F2B'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
F2B

systemctl restart fail2ban

# Set up SSL with Let's Encrypt
if [ ! -d "certbot" ]; then
    mkdir -p certbot/conf certbot/www
    
    # Start nginx temporarily for cert generation
    docker run -d --name temp-nginx \
        -p 80:80 \
        -v $(pwd)/certbot/www:/var/www/certbot \
        nginx:alpine
    
    # Get SSL certificate
    docker run --rm \
        -v $(pwd)/certbot/conf:/etc/letsencrypt \
        -v $(pwd)/certbot/www:/var/www/certbot \
        certbot/certbot certonly --webroot \
        --webroot-path=/var/www/certbot \
        --email admin@aupex.ai \
        --agree-tos \
        --no-eff-email \
        -d aupex.ai \
        -d www.aupex.ai
    
    docker stop temp-nginx
    docker rm temp-nginx
fi

# Configure automated updates
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'UPDATES'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
UPDATES

# Enable automated updates
echo 'APT::Periodic::Update-Package-Lists "1";' > /etc/apt/apt.conf.d/20auto-upgrades
echo 'APT::Periodic::Unattended-Upgrade "1";' >> /etc/apt/apt.conf.d/20auto-upgrades

# Harden SSH
sed -i 's/#PermitRootLogin yes/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd

# Use secure docker-compose
mv docker-compose.prod.secure.yml docker-compose.prod.yml
mv nginx.secure.conf nginx.conf

# Generate secure passwords if not set
if [ ! -f .env ]; then
    cat > .env << 'ENV'
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
CHROMA_TOKEN=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)
ENV
fi

# Start services with new config
docker-compose -f docker-compose.prod.yml up -d

# Wait for services
sleep 10

# Check status
docker ps
ufw status
fail2ban-client status

echo "Security hardening complete!"
echo "Services are now only accessible via Nginx on ports 80/443"
echo "Direct access to databases and internal services is blocked"
EOF
DEPLOY_SCRIPT

chmod +x deploy_secure.sh

echo -e "\n${GREEN}Security hardening scripts created!${NC}"
echo ""
echo "Next steps:"
echo "1. Review the generated files:"
echo "   - docker-compose.prod.secure.yml (secure service configuration)"
echo "   - nginx.secure.conf (hardened nginx with SSL)"
echo "   - deploy_secure.sh (deployment script)"
echo ""
echo "2. Run ./check_server_security.sh to audit current security"
echo "3. Run ./deploy_secure.sh to apply security hardening"
echo ""
echo -e "${YELLOW}IMPORTANT:${NC}"
echo "- Make sure you have SSH key access before disabling password auth"
echo "- The script will get SSL certificates from Let's Encrypt"
echo "- All services will be bound to localhost only"
echo "- Only ports 22, 80, and 443 will be open externally" 