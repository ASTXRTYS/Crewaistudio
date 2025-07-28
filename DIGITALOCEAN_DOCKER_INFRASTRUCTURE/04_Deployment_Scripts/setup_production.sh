#!/bin/bash

# AUREN Production Setup
# Ensures 24/7 operation with auto-recovery

echo "🔧 Setting up production environment..."

# Create data backup script
cat > /root/backup_auren.sh << 'BACKUP'
#!/bin/bash
# Daily backup of AUREN data

BACKUP_DIR="/root/auren-backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker exec auren-postgres pg_dump -U auren_user auren_db > $BACKUP_DIR/postgres.sql

# Backup Redis
docker exec auren-redis redis-cli BGSAVE
sleep 5
docker cp auren-redis:/data/dump.rdb $BACKUP_DIR/redis.rdb

# Backup ChromaDB
docker cp auren-chromadb:/chroma/chroma $BACKUP_DIR/chromadb

# Keep only last 7 days of backups
find /root/auren-backups -type d -mtime +7 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
BACKUP

chmod +x /root/backup_auren.sh

# Schedule daily backups at 3 AM
(crontab -l 2>/dev/null; echo "0 3 * * * /root/backup_auren.sh") | crontab -

# Create log rotation config
cat > /etc/logrotate.d/auren << 'LOGROTATE'
/root/auren-production/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker-compose -f /root/auren-production/docker-compose.prod.yml restart
    endscript
}
LOGROTATE

# Set up automatic Docker cleanup
cat > /root/docker_cleanup.sh << 'CLEANUP'
#!/bin/bash
# Clean up Docker resources weekly

docker system prune -af --volumes
docker volume prune -f
CLEANUP

chmod +x /root/docker_cleanup.sh
(crontab -l 2>/dev/null; echo "0 4 * * 0 /root/docker_cleanup.sh") | crontab -

# Install monitoring tools
apt-get update
apt-get install -y htop iotop nethogs

# Set up swap if not exists (for memory overflow protection)
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# Configure system limits for production
cat >> /etc/sysctl.conf << 'SYSCTL'
# AUREN Production Optimizations
vm.max_map_count=262144
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=65535
fs.file-max=65535
SYSCTL

sysctl -p

# Create knowledge injection script
cat > /root/inject_knowledge.sh << 'INJECT'
#!/bin/bash
# Easy knowledge injection for AI agents

KNOWLEDGE_DIR="/root/auren-production/auren/src/agents/Level 1 knowledge"

if [ -z "$1" ]; then
    echo "Usage: ./inject_knowledge.sh <knowledge_file.md>"
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "Error: File $1 not found"
    exit 1
fi

# Copy knowledge file
cp "$1" "$KNOWLEDGE_DIR/"

# Restart neuroscientist agent to load new knowledge
docker-compose -f /root/auren-production/docker-compose.prod.yml restart auren-api

echo "✅ Knowledge injected: $1"
echo "🔄 AI agents reloading..."
INJECT

chmod +x /root/inject_knowledge.sh

echo "✅ Production setup complete!"
echo ""
echo "🛠️ Available Tools:"
echo "  - Backup: /root/backup_auren.sh"
echo "  - Inject Knowledge: /root/inject_knowledge.sh <file.md>"
echo "  - Auto Deploy: /root/auto_deploy.sh"
echo "  - Health Monitor: Running every minute"
echo "  - Auto Cleanup: Weekly Docker cleanup"
echo "  - Log Rotation: Daily with 7-day retention" 