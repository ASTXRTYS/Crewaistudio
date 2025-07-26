#!/usr/bin/expect -f

# Deploy the ENHANCED dashboard with fixed API URLs

set timeout -1
set password ".HvddX+@6dArsKd"

puts "🚀 Deploying ENHANCED Dashboard to aupex.ai..."

# First, tar the built dashboard
spawn bash -c "cd auren/dashboard_v2 && tar -czf enhanced-dashboard.tar.gz dist/*"
expect eof

# Copy to server
spawn scp auren/dashboard_v2/enhanced-dashboard.tar.gz root@144.126.215.218:/tmp/
expect {
    "*password:*" {
        send "$password\r"
        expect eof
    }
}

# Deploy on server
spawn ssh root@144.126.215.218
expect {
    "*password:*" {
        send "$password\r"
        expect "*#"
    }
}

# Backup old dashboard
send "echo '🔄 Backing up old dashboard...'\r"
expect "*#"

send "rm -rf /usr/share/nginx/html.bak\r"
expect "*#"

send "mv /usr/share/nginx/html /usr/share/nginx/html.bak\r"
expect "*#"

send "mkdir -p /usr/share/nginx/html\r"
expect "*#"

# Extract new dashboard
send "echo '📦 Extracting enhanced dashboard...'\r"
expect "*#"

send "cd /usr/share/nginx/html\r"
expect "*#"

send "tar -xzf /tmp/enhanced-dashboard.tar.gz --strip-components=1\r"
expect "*#"

# Set permissions
send "chown -R www-data:www-data /usr/share/nginx/html\r"
expect "*#"

# Update nginx to enable CORS for API
send "echo '🔧 Updating nginx configuration...'\r"
expect "*#"

send "cat > /etc/nginx/sites-available/aupex.ai << 'EOF'
server {
    listen 80;
    server_name aupex.ai www.aupex.ai 144.126.215.218;

    root /usr/share/nginx/html;
    index index.html;

    # Enable CORS for dashboard
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type' always;

    # Dashboard routes
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API proxy with CORS
    location /api/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Handle preflight
        if (\$request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF\r"
expect "*#"

# Test and reload nginx
send "nginx -t && systemctl reload nginx\r"
expect "*#"

# Clear browser cache hint
send "echo '💡 TIP: Clear your browser cache (Ctrl+Shift+R) to see the enhanced dashboard!'\r"
expect "*#"

# Test the deployment
send "echo '🧪 Testing deployment...'\r"
expect "*#"

send "curl -I http://localhost/\r"
expect "*#"

send "curl -s http://localhost/api/health\r"
expect "*#"

send "echo '\n✨ ENHANCED DASHBOARD DEPLOYED!'\r"
expect "*#"

send "echo '🌟 Visit http://aupex.ai and clear cache to see the stunning visuals!'\r"
expect "*#"

send "exit\r"
expect eof

puts "\n🎉 Enhanced dashboard with all visual improvements is now LIVE!"
puts "🔥 Visit http://aupex.ai (remember to clear browser cache!)" 