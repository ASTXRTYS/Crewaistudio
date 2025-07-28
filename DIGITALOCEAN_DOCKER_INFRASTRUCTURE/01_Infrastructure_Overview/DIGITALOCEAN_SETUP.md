# DIGITALOCEAN DROPLET SETUP GUIDE

## Complete Setup and Configuration of AUREN Infrastructure on DigitalOcean

---

## 🚀 Droplet Specifications

### Current Configuration
- **Droplet Name**: auren-production
- **Region**: NYC3 (New York)
- **Size**: Premium AMD 2vCPU/4GB
- **Storage**: 80GB NVMe SSD
- **OS**: Ubuntu 22.04 LTS
- **IPv4**: 144.126.215.218
- **IPv6**: Enabled
- **VPC**: Default
- **Backups**: Weekly
- **Monitoring**: Enabled

### Monthly Cost
- **Droplet**: $48/month
- **Backups**: $9.60/month
- **Total**: ~$57.60/month

---

## 📋 Initial Server Setup

### 1. Create Droplet via DigitalOcean Console

```
1. Log into DigitalOcean
2. Click "Create" → "Droplets"
3. Choose:
   - Ubuntu 22.04 LTS
   - Premium AMD
   - 2 vCPU / 4GB RAM / 80GB SSD
   - NYC3 datacenter
   - Enable backups
   - Add SSH key
4. Create Droplet
```

### 2. Initial SSH Connection

```bash
# First connection
ssh root@144.126.215.218

# Update system
apt update && apt upgrade -y

# Set timezone
timedatectl set-timezone UTC

# Configure hostname
hostnamectl set-hostname auren-production
```

### 3. Create Swap File (Important!)

```bash
# Create 4GB swap
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Configure swappiness
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl -p
```

---

## 🔒 Security Hardening

### 1. Configure Firewall

```bash
# Enable UFW
ufw --force enable

# Allow SSH
ufw allow 22/tcp

# Allow HTTP
ufw allow 80/tcp

# Allow HTTPS
ufw allow 443/tcp

# Allow Kafka UI (temporary, restrict later)
ufw allow 8081/tcp

# Check status
ufw status
```

### 2. Secure SSH

```bash
# Edit SSH config
nano /etc/ssh/sshd_config

# Add/modify these lines:
PermitRootLogin yes  # Change to 'no' after creating user
PasswordAuthentication no
PubkeyAuthentication yes
ClientAliveInterval 300
ClientAliveCountMax 2

# Restart SSH
systemctl restart sshd
```

### 3. Install Fail2ban

```bash
# Install
apt install fail2ban -y

# Configure
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit jail.local
nano /etc/fail2ban/jail.local

# Add under [sshd]:
enabled = true
maxretry = 3
bantime = 3600

# Start service
systemctl enable fail2ban
systemctl start fail2ban
```

---

## 🐳 Docker Installation

### 1. Install Docker Engine

```bash
# Remove old versions
apt remove docker docker-engine docker.io containerd runc

# Install prerequisites
apt update
apt install ca-certificates curl gnupg lsb-release -y

# Add Docker GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt update
apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### 2. Configure Docker

```bash
# Configure Docker daemon
cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
EOF

# Restart Docker
systemctl restart docker
```

---

## 🔧 System Optimization

### 1. Kernel Parameters

```bash
# Edit sysctl.conf
nano /etc/sysctl.conf

# Add optimizations:
# Network
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1

# Memory
vm.max_map_count = 262144
vm.overcommit_memory = 1

# File handles
fs.file-max = 65535

# Apply changes
sysctl -p
```

### 2. Increase File Limits

```bash
# Edit limits.conf
nano /etc/security/limits.conf

# Add:
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
```

### 3. Install Essential Tools

```bash
# System monitoring
apt install htop iotop nethogs -y

# Network tools
apt install net-tools dnsutils curl wget -y

# Development tools
apt install git vim build-essential -y

# Compression
apt install zip unzip -y

# Process management
apt install supervisor -y
```

---

## 📁 Directory Structure

### Create Project Directories

```bash
# Main project directory
mkdir -p /root/auren-production

# Backup directory
mkdir -p /root/backups

# Scripts directory
mkdir -p /root/scripts

# SSL certificates (for future)
mkdir -p /etc/letsencrypt
```

---

## 🌐 Domain Configuration

### 1. DNS Setup (Cloudflare)

```
A Record:
- Name: @
- Value: 144.126.215.218
- TTL: Auto
- Proxy: OFF (for now)

A Record:
- Name: www
- Value: 144.126.215.218
- TTL: Auto
- Proxy: OFF
```

### 2. Test DNS

```bash
# From server
dig aupex.ai
nslookup aupex.ai

# Check propagation
curl -I http://aupex.ai
```

---

## 🔄 Automated Backups

### 1. DigitalOcean Backups

- Weekly automated backups enabled
- Stored for 4 weeks
- Full system snapshots

### 2. Custom Backup Script

```bash
# Create backup script
cat > /root/scripts/backup_auren.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker exec auren-postgres pg_dump -U auren_user auren_db | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Backup Redis
docker exec auren-redis redis-cli BGSAVE
sleep 5
docker cp auren-redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Backup configs
tar -czf $BACKUP_DIR/configs_$DATE.tar.gz /root/auren-production/

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /root/scripts/backup_auren.sh

# Add to crontab
crontab -e
# Add: 0 3 * * * /root/scripts/backup_auren.sh
```

---

## 📊 Monitoring Setup

### 1. DigitalOcean Monitoring

- CPU, Memory, Disk metrics
- Network bandwidth
- Alert policies available

### 2. Custom Monitoring

```bash
# Create monitoring script
cat > /root/scripts/monitor_health.sh << 'EOF'
#!/bin/bash

# Check if services are running
if ! docker ps | grep -q auren-api; then
    echo "ALERT: AUREN API is down!"
    # Add notification method here
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "ALERT: Disk usage is at $DISK_USAGE%"
fi

# Check memory
MEM_FREE=$(free -m | awk 'NR==2{print $4}')
if [ $MEM_FREE -lt 500 ]; then
    echo "ALERT: Low memory - only $MEM_FREE MB free"
fi
EOF

chmod +x /root/scripts/monitor_health.sh

# Add to crontab for every 5 minutes
# */5 * * * * /root/scripts/monitor_health.sh
```

---

## 🚨 Droplet Management

### Resize Droplet (When Needed)

```bash
# From DigitalOcean console:
1. Power off droplet
2. Resize → Choose new size
3. Resize droplet
4. Power on

# Or via CLI:
doctl compute droplet-action resize <droplet-id> --size s-4vcpu-8gb --wait
```

### Create Snapshot

```bash
# Manual snapshot
doctl compute droplet-action snapshot <droplet-id> --snapshot-name "auren-before-update"

# Or from console:
1. Select droplet
2. Snapshots → Take snapshot
```

### Enable Floating IP (Optional)

```bash
# For high availability
1. Networking → Floating IPs
2. Assign to droplet
3. Update DNS to floating IP
```

---

## 🔐 Environment Variables

### Create .env file

```bash
# In /root/auren-production/
cat > .env << EOF
# API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Database
POSTGRES_USER=auren_user
POSTGRES_PASSWORD=auren_password_2024
POSTGRES_DB=auren_db

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Environment
ENVIRONMENT=production
EOF

chmod 600 .env
```

---

## 📈 Performance Monitoring

### Setup htop for monitoring

```bash
# Run htop
htop

# Key shortcuts:
# F6 - Sort by column
# F5 - Tree view
# F9 - Kill process
# F10 - Quit
```

### Monitor Docker resources

```bash
# Real-time stats
docker stats

# Disk usage
df -h
du -sh /var/lib/docker/

# Network connections
netstat -tulpn
```

---

## 🔄 Maintenance Tasks

### Weekly Tasks
1. Check disk space
2. Review logs
3. Update system packages
4. Check backup integrity

### Monthly Tasks
1. Review resource usage
2. Update Docker images
3. Security audit
4. Performance optimization

### Quarterly Tasks
1. Major system updates
2. Capacity planning
3. Disaster recovery test
4. Cost optimization review

---

## 📞 Support Resources

### DigitalOcean Support
- **Ticket System**: Available 24/7
- **Community**: https://www.digitalocean.com/community
- **Documentation**: https://docs.digitalocean.com

### Monitoring Alerts
- Set up email alerts in DigitalOcean console
- Configure Slack/Discord webhooks for critical alerts

---

## 🎯 Next Steps After Setup

1. Deploy AUREN application
2. Configure SSL certificates
3. Set up continuous deployment
4. Implement monitoring alerts
5. Document custom configurations

---

*This setup provides a secure, optimized foundation for running AUREN in production. Regular maintenance and monitoring ensure continued reliability and performance.* 