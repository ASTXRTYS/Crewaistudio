# NGINX CONFIGURATION STANDARD
## Critical Information for Website Deployments

*Created: January 28, 2025*  
*Updated: January 29, 2025 - API proxy updated for NEUROS*  
*Purpose: Prevent wrong directory deployments and document API routing*

---

## ⚠️ CRITICAL: ALWAYS CHECK NGINX ROOT BEFORE DEPLOYMENT

### Current Production Configuration

```nginx
# File: /etc/nginx/sites-enabled/aupex.ai
server {
    listen 80;
    server_name aupex.ai www.aupex.ai 144.126.215.218;
    
    # IMPORTANT: This is where files must be deployed!
    root /usr/share/nginx/html;  # <-- NOT /var/www/html
    
    index index.html index.htm;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # API proxy - Updated to NEUROS on port 8000
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket headers
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # WebSocket endpoint - Updated to NEUROS on port 8000
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

---

## 🔍 How to Check Nginx Root Directory

### Before ANY website deployment, run:

```bash
# Method 1: Direct grep
grep -h "root" /etc/nginx/sites-enabled/* | grep -v "#"

# Method 2: With site identification  
grep -H "root" /etc/nginx/sites-enabled/*

# Method 3: Check specific site
cat /etc/nginx/sites-enabled/aupex.ai | grep "root"
```

### Expected Output:
```
root /usr/share/nginx/html;
```

---

## 📁 Directory Structure

```
/usr/share/nginx/html/          # <-- CORRECT deployment directory
├── index.html                  # Main page
├── agents/                     # Agent pages
│   ├── index.html
│   └── neuroscientist.html
├── js/                         # JavaScript files
│   ├── main.js
│   └── neuroscientist.js
└── styles/                     # CSS files
    ├── main.css
    └── neuroscientist.css

/var/www/html/                  # <-- WRONG directory (not used!)
```

---

## 🚀 Deployment Commands

### CORRECT Deployment:
```bash
# Deploy to the RIGHT directory
sshpass -p '.HvddX+@6dArsKd' scp -r website_files/* root@144.126.215.218:/usr/share/nginx/html/

# Set correct permissions
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'chown -R www-data:www-data /usr/share/nginx/html/'
```

### WRONG Deployment (DO NOT USE):
```bash
# This deploys to wrong directory!
scp -r files/* root@server:/var/www/html/  # ❌ WRONG!
```

---

## ✅ Verification Steps

### 1. Check Files Are in Correct Location
```bash
ssh root@144.126.215.218 'ls -la /usr/share/nginx/html/'
```

### 2. Verify Website Content
```bash
# Check for new website markers
curl -s http://aupex.ai | grep -E "(Three.js|AUREN - Neural)"

# Should see:
# <title>AUREN - Neural Optimization Intelligence</title>
# <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
```

### 3. Visual Check
- Open http://aupex.ai in browser
- Verify 3D animations are working
- Check navigation menu appears

---

## 🔧 Troubleshooting

### If Website Shows Wrong Version:

1. **Check which directory nginx is using:**
   ```bash
   nginx -T | grep -A5 "server_name aupex.ai"
   ```

2. **Check both directories:**
   ```bash
   ls -la /usr/share/nginx/html/index.html
   ls -la /var/www/html/index.html
   ```

3. **Compare file contents:**
   ```bash
   head -5 /usr/share/nginx/html/index.html
   ```

4. **Reload nginx after changes:**
   ```bash
   systemctl reload nginx
   ```

---

## 📋 Deployment Checklist

Before marking website "deployed":

- [ ] Checked nginx root directory configuration
- [ ] Deployed files to `/usr/share/nginx/html/`
- [ ] Set correct ownership (`www-data:www-data`)
- [ ] Verified with `curl` command
- [ ] Checked in actual browser
- [ ] Confirmed 3D animations working
- [ ] Took screenshot for documentation

---

## 🚨 Common Mistakes

1. **Assuming `/var/www/html`** - Always check actual config
2. **Not reloading nginx** - Changes need `systemctl reload nginx`
3. **Wrong permissions** - Files must be owned by `www-data`
4. **Not verifying** - Always check the live site

---

## 📝 Standard Operating Procedure

```bash
#!/bin/bash
# Standard website deployment script

# 1. Get nginx root
NGINX_ROOT=$(ssh root@144.126.215.218 "grep -h 'root' /etc/nginx/sites-enabled/aupex.ai | awk '{print \$2}' | tr -d ';'")
echo "Nginx root: $NGINX_ROOT"

# 2. Deploy files
scp -r website_files/* root@144.126.215.218:$NGINX_ROOT/

# 3. Fix permissions
ssh root@144.126.215.218 "chown -R www-data:www-data $NGINX_ROOT"

# 4. Reload nginx
ssh root@144.126.215.218 "systemctl reload nginx"

# 5. Verify deployment
if curl -s http://aupex.ai | grep -q "Three.js"; then
    echo "✅ Deployment successful"
else
    echo "❌ WRONG VERSION DEPLOYED!"
    exit 1
fi
```

---

*This document exists because we deployed to the wrong directory. Follow these procedures to ensure it never happens again.* 