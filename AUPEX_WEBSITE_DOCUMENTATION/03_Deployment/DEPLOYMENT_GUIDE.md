# AUPEX.AI DEPLOYMENT GUIDE

## Complete Guide for Deploying the AUREN Website

---

## 🚀 Quick Deployment

### One-Command Deploy:
```bash
./deploy_new_website.sh
```

This script handles everything automatically. However, understanding the manual process is important for troubleshooting.

---

## 📋 Pre-Deployment Checklist

### Prerequisites:
- [ ] SSH access to 144.126.215.218
- [ ] Root or sudo privileges on server
- [ ] Local files in `auren/dashboard_v2/`
- [ ] Internet connection stable

### Verify Local Files:
```bash
# Check that website files exist
ls -la auren/dashboard_v2/
ls -la auren/dashboard_v2/agents/
ls -la auren/dashboard_v2/styles/
ls -la auren/dashboard_v2/js/
```

---

## 🔧 Manual Deployment Steps

### Step 1: Connect to Server
```bash
ssh root@144.126.215.218
```

### Step 2: Backup Current Website (Optional)
```bash
# On server
cd /usr/share/nginx/html
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz ./*
mv backup-*.tar.gz /root/backups/
```

### Step 3: Upload New Files
```bash
# From local machine
scp -r auren/dashboard_v2/* root@144.126.215.218:/usr/share/nginx/html/
```

### Step 4: Set Correct Permissions
```bash
# On server
cd /usr/share/nginx/html
chown -R www-data:www-data .
chmod -R 755 .
find . -type f -exec chmod 644 {} \;
```

### Step 5: Clear Nginx Cache
```bash
# On server
nginx -s reload
```

### Step 6: Verify Deployment
```bash
# Test main pages
curl -I http://aupex.ai
curl -I http://aupex.ai/agents/
curl -I http://aupex.ai/agents/neuroscientist.html
```

---

## 🐳 Docker Deployment (Alternative)

### Using Docker Compose:
```yaml
# Add to docker-compose.yml
nginx-web:
  image: nginx:alpine
  container_name: auren-nginx-web
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./auren/dashboard_v2:/usr/share/nginx/html:ro
    - ./nginx-website.conf:/etc/nginx/conf.d/default.conf:ro
  restart: unless-stopped
```

### Deploy with Docker:
```bash
docker-compose up -d nginx-web
```

---

## 🔍 Deployment Verification

### 1. Check Server Response:
```bash
# HTTP status should be 200
curl -s -o /dev/null -w "%{http_code}" http://aupex.ai
```

### 2. Verify Resources Load:
```bash
# Check CSS loads
curl -I http://aupex.ai/styles/main.css

# Check JS loads
curl -I http://aupex.ai/js/main.js
```

### 3. Test API Endpoints:
```bash
# Health check
curl http://aupex.ai/api/health

# WebSocket test (should return 426 or 101)
curl -I -H "Upgrade: websocket" http://aupex.ai/ws
```

### 4. Browser Verification:
1. Open http://aupex.ai in browser
2. Check browser console for errors (F12)
3. Verify 3D animations load
4. Test navigation between pages

---

## 🛠️ Troubleshooting

### Common Issues:

#### 1. 404 Not Found
```bash
# Check nginx root directory
nginx -T | grep root

# Verify files exist
ls -la /usr/share/nginx/html/
```

#### 2. 403 Forbidden
```bash
# Fix permissions
chown -R www-data:www-data /usr/share/nginx/html
chmod -R 755 /usr/share/nginx/html
```

#### 3. Blank Page
```bash
# Check nginx error logs
tail -f /var/log/nginx/error.log

# Check browser console for JS errors
# Clear browser cache (Ctrl+Shift+R)
```

#### 4. API Not Working
```bash
# Check if API service is running
docker ps | grep auren-api

# Check nginx proxy configuration
grep -A 5 "location /api" /etc/nginx/sites-enabled/default
```

---

## 🔄 Rollback Procedure

### If deployment fails:

#### Option 1: Quick Rollback
```bash
# On server
cd /usr/share/nginx/html
rm -rf *
tar -xzf /root/backups/backup-[timestamp].tar.gz
nginx -s reload
```

#### Option 2: Git Rollback
```bash
# On local machine
git checkout [previous-commit-hash]
./deploy_new_website.sh
```

---

## 📊 Post-Deployment Tasks

### 1. Monitor Logs:
```bash
# Watch nginx access logs
tail -f /var/log/nginx/access.log

# Watch error logs
tail -f /var/log/nginx/error.log
```

### 2. Performance Check:
```bash
# Test load time
time curl -s http://aupex.ai > /dev/null

# Check resource sizes
curl -s http://aupex.ai | wc -c
```

### 3. Security Scan:
```bash
# Check headers
curl -I http://aupex.ai

# SSL check (when enabled)
# openssl s_client -connect aupex.ai:443
```

---

## 🚨 Emergency Procedures

### If Website is Down:

1. **Check Nginx Status:**
```bash
systemctl status nginx
systemctl restart nginx
```

2. **Check Disk Space:**
```bash
df -h
# Clear logs if needed
truncate -s 0 /var/log/nginx/*.log
```

3. **Check DNS:**
```bash
dig aupex.ai
nslookup aupex.ai
```

4. **Restart Everything:**
```bash
docker-compose restart
systemctl restart nginx
```

---

## 📈 Continuous Deployment

### GitHub Actions (Future):
```yaml
name: Deploy Website
on:
  push:
    branches: [main]
    paths:
      - 'auren/dashboard_v2/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Server
        run: |
          ./deploy_new_website.sh
```

### Monitoring Integration:
- Set up uptime monitoring
- Configure alerts for downtime
- Track deployment metrics

---

## 📝 Deployment Log Template

```
Date: [DATE]
Deployer: [NAME]
Version: [COMMIT_HASH]
Changes: [BRIEF_DESCRIPTION]

Pre-deployment checks:
- [ ] Backup created
- [ ] API health verified
- [ ] Traffic low

Deployment:
- [ ] Files uploaded
- [ ] Permissions set
- [ ] Nginx reloaded

Post-deployment:
- [ ] Website accessible
- [ ] All pages load
- [ ] API functional
- [ ] No console errors

Issues: [ANY_ISSUES]
Resolution: [HOW_RESOLVED]
```

---

*Always test deployments during low-traffic periods and have a rollback plan ready!* 