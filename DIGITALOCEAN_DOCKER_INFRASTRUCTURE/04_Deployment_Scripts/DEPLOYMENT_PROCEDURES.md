# DEPLOYMENT PROCEDURES

## Step-by-Step Guide for Deploying AUREN to Production

---

## 🚀 Deployment Overview

### Deployment Methods
1. **One-Command Deploy** - Automated via DEPLOY_NOW.sh
2. **Manual Deploy** - Step-by-step control
3. **Rolling Update** - Zero-downtime deployment
4. **Emergency Deploy** - Quick fixes

---

## 📋 Pre-Deployment Checklist

### Before Every Deployment:
- [ ] All tests passing locally
- [ ] Environment variables updated
- [ ] Database migrations prepared
- [ ] Backup completed
- [ ] Team notified
- [ ] Monitoring alerts paused
- [ ] Traffic is low (optional)

### First-Time Setup:
- [ ] Server provisioned
- [ ] Docker installed
- [ ] Domain configured
- [ ] Firewall rules set
- [ ] SSH keys added
- [ ] Swap file created

---

## 🎯 One-Command Deployment

### Using DEPLOY_NOW.sh

```bash
# From your local machine
cd /path/to/project
./DEPLOY_NOW.sh
```

### What It Does:
1. Builds deployment package
2. Uploads to server
3. Stops current services
4. Deploys new version
5. Starts services
6. Verifies health

### Expected Output:
```
╔══════════════════════════════════════════════════════════╗
║                    🚀 AUREN DEPLOY                       ║
║         Deploying to aupex.ai @ 144.126.215.218         ║
╚══════════════════════════════════════════════════════════╝

[1/6] Building deployment package...
[2/6] Uploading to server...
[3/6] Stopping services...
[4/6] Deploying new version...
[5/6] Starting services...
[6/6] Verifying deployment...

✅ Deployment successful!
🌐 Site: http://aupex.ai
📊 Health: http://aupex.ai/api/health
```

---

## 🔧 Manual Deployment Steps

### Step 1: Prepare Deployment Package

```bash
# Create deployment directory
mkdir -p deployment-$(date +%Y%m%d-%H%M%S)
cd deployment-*

# Copy necessary files
cp -r ../docker-compose.prod.yml .
cp -r ../auren .
cp -r ../sql .
cp -r ../nginx.conf .
cp ../.env.production .env

# Create tarball
cd ..
tar -czf deployment.tar.gz deployment-*/
```

### Step 2: Upload to Server

```bash
# Upload deployment package
scp deployment.tar.gz root@144.126.215.218:/tmp/

# Connect to server
ssh root@144.126.215.218
```

### Step 3: Extract and Prepare

```bash
# On server
cd /root/auren-production

# Backup current version
cp -r . ../auren-backup-$(date +%Y%m%d-%H%M%S)

# Extract new version
tar -xzf /tmp/deployment.tar.gz
cp -r deployment-*/* .
rm -rf deployment-*
```

### Step 4: Stop Current Services

```bash
# Stop services gracefully
docker-compose -f docker-compose.prod.yml stop

# Wait for graceful shutdown
sleep 10

# Force stop if needed
docker-compose -f docker-compose.prod.yml down
```

### Step 5: Deploy New Version

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Start services with new config
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### Step 6: Verify Deployment

```bash
# Check service health
curl http://localhost:8080/health

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs --tail=50

# Test from outside
curl http://aupex.ai/api/health
```

---

## 🔄 Rolling Update Deployment

### For Zero Downtime

#### Step 1: Deploy Database Changes First
```bash
# If there are migrations
docker exec auren-postgres psql -U auren_user -d auren_db -f /migrations/new_migration.sql
```

#### Step 2: Deploy API Service
```bash
# Scale up new version
docker-compose -f docker-compose.prod.yml up -d --scale auren-api=2 --no-recreate auren-api

# Wait for health
sleep 30

# Remove old container
docker stop auren-api_1
docker rm auren-api_1
```

#### Step 3: Deploy Frontend
```bash
# Update static files
docker-compose -f docker-compose.prod.yml up -d nginx
```

---

## 🚨 Emergency Deployment

### For Critical Fixes

```bash
# Quick deploy script
ssh root@144.126.215.218 << 'EOF'
cd /root/auren-production
git pull  # If using git
docker-compose -f docker-compose.prod.yml restart auren-api
EOF
```

### Rollback Procedure
```bash
# Connect to server
ssh root@144.126.215.218

# Restore backup
cd /root
mv auren-production auren-production-failed
mv auren-backup-[timestamp] auren-production
cd auren-production

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📦 Service-Specific Deployments

### Deploy Only API
```bash
docker-compose -f docker-compose.prod.yml up -d --no-deps auren-api
```

### Deploy Only Frontend
```bash
# Copy new files
scp -r auren/dashboard_v2/* root@144.126.215.218:/root/auren-production/auren/dashboard_v2/

# Restart nginx
ssh root@144.126.215.218 "docker-compose -f /root/auren-production/docker-compose.prod.yml restart nginx"
```

### Deploy Only Database Changes
```bash
# Copy migration files
scp migrations/*.sql root@144.126.215.218:/tmp/

# Run migrations
ssh root@144.126.215.218 << 'EOF'
docker exec -i auren-postgres psql -U auren_user -d auren_db < /tmp/migration.sql
EOF
```

---

## 🔍 Post-Deployment Verification

### Health Checks
```bash
# API Health
curl http://aupex.ai/api/health | jq .

# Service Status
docker-compose -f docker-compose.prod.yml ps

# Resource Usage
docker stats --no-stream

# Check Logs
docker-compose -f docker-compose.prod.yml logs --tail=100 | grep ERROR
```

### Functional Tests
```bash
# Test main endpoints
curl http://aupex.ai/
curl http://aupex.ai/api/memory/stats
curl http://aupex.ai/api/knowledge-graph/data

# Test WebSocket
wscat -c ws://aupex.ai/ws/dashboard/test
```

### Performance Tests
```bash
# Response time
time curl http://aupex.ai/api/health

# Load test (careful in production!)
ab -n 100 -c 10 http://aupex.ai/api/health
```

---

## 📊 Deployment Metrics

### Track These Metrics:
- Deployment duration
- Downtime (if any)
- Error rate post-deployment
- Response time changes
- Resource usage changes

### Log Deployment
```bash
# Create deployment log
cat >> /root/deployment.log << EOF
Date: $(date)
Version: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
Deployer: $(whoami)
Duration: X minutes
Issues: None
EOF
```

---

## 🛠️ Troubleshooting Deployments

### Common Issues:

#### 1. Service Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs [service-name]

# Check resources
df -h  # Disk space
free -m  # Memory

# Rebuild if needed
docker-compose -f docker-compose.prod.yml build --no-cache [service-name]
```

#### 2. Database Connection Failed
```bash
# Test connection
docker exec auren-api pg_isready -h postgres -U auren_user

# Check network
docker network inspect auren-network

# Restart in order
docker-compose -f docker-compose.prod.yml restart postgres
sleep 10
docker-compose -f docker-compose.prod.yml restart auren-api
```

#### 3. Nginx 502 Bad Gateway
```bash
# Check if API is running
docker ps | grep auren-api

# Check nginx config
docker exec auren-nginx nginx -t

# Restart both
docker-compose -f docker-compose.prod.yml restart auren-api nginx
```

---

## 🔐 Security During Deployment

### Best Practices:
1. Never commit secrets to git
2. Use .env files for sensitive data
3. Rotate secrets after deployment
4. Check for exposed ports
5. Verify firewall rules

### Post-Deploy Security Check:
```bash
# Check exposed ports
netstat -tulpn | grep LISTEN

# Check running processes
ps aux | grep -v grep | grep -E "(docker|python|node)"

# Verify file permissions
ls -la /root/auren-production/.env
```

---

## 📝 Deployment Documentation

### After Each Deployment:
1. Update deployment log
2. Document any issues
3. Update runbooks if needed
4. Notify team of completion

### Deployment Record Template:
```markdown
## Deployment - [DATE]

**Version**: [COMMIT/TAG]
**Deployer**: [NAME]
**Duration**: [X] minutes
**Downtime**: [0] seconds

### Changes:
- Feature X added
- Bug Y fixed
- Performance improvement Z

### Issues:
- None

### Rollback Required**: No

### Notes:
- [Any special notes]
```

---

## 🚀 Advanced Deployment Strategies

### Blue-Green Deployment
```bash
# Prepare green environment
docker-compose -f docker-compose.green.yml up -d

# Test green environment
curl http://localhost:8081/health

# Switch traffic
sed -i 's/8080/8081/g' nginx.conf
docker-compose restart nginx

# Remove blue environment
docker-compose -f docker-compose.blue.yml down
```

### Canary Deployment
```bash
# Deploy canary version (10% traffic)
# Requires load balancer configuration
```

### Feature Flags
```python
# In application code
if feature_flags.get('new_feature_enabled'):
    # New code path
else:
    # Old code path
```

---

## 📅 Deployment Schedule

### Recommended Windows:
- **Regular Updates**: Tuesday-Thursday, 10 AM - 2 PM
- **Major Updates**: Weekend mornings
- **Emergency Fixes**: Anytime (with approval)

### Avoid:
- Friday deployments (unless critical)
- Holiday periods
- High-traffic times

---

*Following these procedures ensures consistent, reliable deployments with minimal risk and downtime.* 