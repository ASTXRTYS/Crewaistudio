#!/usr/bin/expect -f

# AUREN Final Deployment - Deploy the new dashboard

set timeout -1
set password ".HvddX+@6dArsKd"

spawn ssh root@144.126.215.218

expect {
    "*password:*" {
        send "$password\r"
        expect "*#"
    }
}

# Navigate to deployment directory
send "cd /root/auren-production\r"
expect "*#"

# Stop old dashboard container
send "docker stop auren-dashboard && docker rm auren-dashboard\r"
expect "*#"

# Copy the new dashboard build
send "rm -rf /usr/share/nginx/html/*\r"
expect "*#"

send "cp -r auren/dashboard_v2/dist/* /usr/share/nginx/html/\r"
expect "*#"

# Update nginx config for the new setup
send "cat > /etc/nginx/sites-available/aupex.ai << 'EOF'
server {
    listen 80;
    server_name aupex.ai www.aupex.ai 144.126.215.218;

    root /usr/share/nginx/html;
    index index.html;

    # Dashboard routes
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
    }
}
EOF\r"
expect "*#"

# Enable the site
send "ln -sf /etc/nginx/sites-available/aupex.ai /etc/nginx/sites-enabled/\r"
expect "*#"

send "rm -f /etc/nginx/sites-enabled/default\r"
expect "*#"

# Test and reload nginx
send "nginx -t && systemctl reload nginx\r"
expect "*#"

# Check all services
send "echo '=== AUREN Services Status ==='\r"
expect "*#"

send "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep auren\r"
expect "*#"

# Test the API
send "echo '=== API Health Check ==='\r"
expect "*#"

send "curl -s http://localhost:8080/health\r"
expect "*#"

# Show the website status
send "echo '=== Website Status ==='\r"
expect "*#"

send "curl -sI http://aupex.ai | head -5\r"
expect "*#"

send "echo '\n✅ DEPLOYMENT COMPLETE!'\r"
expect "*#"

send "echo 'Access your dashboard at: http://aupex.ai'\r"
expect "*#"

send "exit\r"
expect eof

puts "\n🎉 AUREN IS LIVE AT http://aupex.ai!" 