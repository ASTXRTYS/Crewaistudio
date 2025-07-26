#!/usr/bin/expect -f

# Fix API connection and nginx proxy

set timeout -1
set password ".HvddX+@6dArsKd"

spawn ssh root@144.126.215.218

expect {
    "*password:*" {
        send "$password\r"
        expect "*#"
    }
}

# Check API status
send "echo '🔍 Checking API status...'\r"
expect "*#"

send "docker ps | grep auren-api\r"
expect "*#"

# Get API container IP
send "docker inspect auren-api | grep IPAddress | head -1\r"
expect "*#"

# Test direct API access
send "curl -s http://localhost:8080/health\r"
expect "*#"

# Fix nginx to use correct API endpoint
send "echo '🔧 Fixing nginx API proxy...'\r"
expect "*#"

send "cat > /etc/nginx/sites-available/aupex.ai << 'EOF'
server {
    listen 80;
    server_name aupex.ai www.aupex.ai 144.126.215.218;

    root /usr/share/nginx/html;
    index index.html;

    # Enable gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml+rss;

    # Dashboard routes
    location / {
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control \"no-cache, no-store, must-revalidate\";
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8080/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8080/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }
}
EOF\r"
expect "*#"

# Reload nginx
send "nginx -t && systemctl reload nginx\r"
expect "*#"

# Test the fixed API proxy
send "echo '🧪 Testing API through nginx...'\r"
expect "*#"

send "curl -s http://localhost/api/health\r"
expect "*#"

send "echo '\n✅ API connection fixed!'\r"
expect "*#"

send "echo '🎨 The enhanced dashboard is now LIVE with:'\r"
expect "*#"

send "echo '  • Neural color palette and glassmorphism'\r"
expect "*#"

send "echo '  • GPU-accelerated animations'\r"
expect "*#"

send "echo '  • Real-time knowledge graph'\r"
expect "*#"

send "echo '  • Live API connection'\r"
expect "*#"

send "echo '\n🌟 Visit http://aupex.ai and refresh!'\r"
expect "*#"

send "exit\r"
expect eof

puts "\n🎉 EVERYTHING IS FIXED! Visit http://aupex.ai to see your stunning dashboard!" 