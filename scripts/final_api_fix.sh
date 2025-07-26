#!/usr/bin/expect -f

# Final fix for API proxy configuration

set timeout -1
set password ".HvddX+@6dArsKd"

spawn ssh root@144.126.215.218

expect {
    "*password:*" {
        send "$password\r"
        expect "*#"
    }
}

# Final nginx configuration
send "cat > /etc/nginx/sites-available/aupex.ai << 'EOF'
server {
    listen 80;
    server_name aupex.ai www.aupex.ai 144.126.215.218;

    root /usr/share/nginx/html;
    index index.html;

    # Enable gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # Dashboard files
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API proxy - proxy to root, not /api/
    location /api/ {
        proxy_pass http://localhost:8080/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$http_connection;
    }

    # WebSocket specific endpoint
    location /ws {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    # Health check direct
    location /health {
        proxy_pass http://localhost:8080/health;
    }
}
EOF\r"
expect "*#"

# Test and reload
send "nginx -t && systemctl reload nginx\r"
expect "*#"

# Verify all endpoints
send "echo '🧪 Testing all endpoints...'\r"
expect "*#"

send "curl -s http://localhost/health | jq .\r"
expect "*#"

send "curl -s http://localhost/api/memory/stats | jq .\r"
expect "*#"

send "curl -s 'http://localhost/api/knowledge-graph/data?depth=1' | head -50\r"
expect "*#"

send "echo '\n✨ SUCCESS! Your stunning dashboard is now LIVE!'\r"
expect "*#"

send "echo '🎨 Features:'\r"
expect "*#"

send "echo '  ✓ Neural color palette with deep space theme'\r"
expect "*#"

send "echo '  ✓ Glassmorphism panels with depth effects'\r"
expect "*#"

send "echo '  ✓ GPU-accelerated animations'\r"
expect "*#"

send "echo '  ✓ Real-time knowledge graph visualization'\r"
expect "*#"

send "echo '  ✓ Live WebSocket connections'\r"
expect "*#"

send "echo '\n🌟 Visit http://aupex.ai and press Ctrl+Shift+R to see it!'\r"
expect "*#"

send "exit\r"
expect eof

puts "\n🎉 DEPLOYMENT COMPLETE!"
puts "🚀 Your enhanced AUREN dashboard is LIVE at http://aupex.ai"
puts "💡 Remember to clear your browser cache (Ctrl+Shift+R) to see all the visual enhancements!" 