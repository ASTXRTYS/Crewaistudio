#!/bin/bash

echo "🔧 Fixing Nginx Configuration"
echo "============================="

# Create nginx config
cat > nginx-website.conf << 'EOF'
server {
    listen 80;
    server_name aupex.ai www.aupex.ai;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Main site
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://auren-api:8080/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket proxy
    location /ws {
        proxy_pass http://auren-api:8080/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Create expect script
cat > fix_nginx.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 300
set password ".HvddX+@6dArsKd"

spawn scp nginx-website.conf root@144.126.215.218:/root/
expect {
    "password:" {
        send "$password\r"
        exp_continue
    }
    "100%" {
        puts "\n✅ Config uploaded!"
    }
    eof
}

spawn ssh root@144.126.215.218
expect {
    "password:" {
        send "$password\r"
        expect "# "
    }
}

send "cd /root/auren-production\r"
expect "# "

send "echo 'Updating nginx configuration...'\r"
expect "# "

send "cp /root/nginx-website.conf nginx.conf\r"
expect "# "

send "echo 'Checking if website files exist...'\r"
expect "# "

send "ls -la auren/dashboard_v2/\r"
expect "# "

send "echo 'Restarting nginx with new config...'\r"
expect "# "

send "docker-compose -f docker-compose.prod.yml restart nginx\r"
expect "# "

send "sleep 5\r"
expect "# "

send "echo 'Testing nginx...'\r"
expect "# "

send "docker logs auren-nginx --tail=20\r"
expect "# "

send "echo '✅ Nginx fixed!'\r"
expect "# "

send "exit\r"
expect eof
EOF

chmod +x fix_nginx.exp
./fix_nginx.exp
rm fix_nginx.exp

echo ""
echo "✅ NGINX CONFIGURATION FIXED!"
echo ""
echo "Try visiting: http://aupex.ai" 