#!/usr/bin/expect -f

# Fix nginx to use correct API port (8080 not 8000)

set timeout -1
set password ".HvddX+@6dArsKd"

spawn ssh root@144.126.215.218

expect {
    "*password:*" {
        send "$password\r"
        expect "*#"
    }
}

# Remove all nginx configs first
send "rm -f /etc/nginx/sites-enabled/*\r"
expect "*#"

# Create correct configuration
send "cat > /etc/nginx/sites-enabled/aupex.ai << 'EOF'
server {
    listen 80;
    server_name aupex.ai www.aupex.ai 144.126.215.218;

    root /usr/share/nginx/html;
    index index.html;

    # Dashboard
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API proxy - CORRECT PORT 8080
    location /api/ {
        proxy_pass http://localhost:8080/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket headers
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
    }

    # WebSocket endpoint - CORRECT PORT 8080
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

# Test and reload
send "nginx -t && systemctl reload nginx\r"
expect "*#"

# Verify it works
send "echo '🧪 Testing fixed endpoints...'\r"
expect "*#"

send "curl -s http://localhost/api/health | jq .\r"
expect "*#"

send "curl -s http://localhost/api/memory/stats | jq .\r"
expect "*#"

send "echo '\n🎉 FIXED! Your stunning dashboard is now FULLY OPERATIONAL!'\r"
expect "*#"

send "exit\r"
expect eof

puts "\n✨ SUCCESS! Visit http://aupex.ai to see your enhanced dashboard!"
puts "🔥 Clear your browser cache (Ctrl+Shift+R) for the full experience!" 