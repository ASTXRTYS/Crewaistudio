#!/bin/bash

echo "🔄 Restarting AUREN Services"
echo "============================"

SERVER_IP="144.126.215.218"
PASSWORD=".HvddX+@6dArsKd"

# Create expect script
cat > restart.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 60
set password [lindex $argv 0]

spawn ssh root@144.126.215.218

expect {
    "password:" {
        send "$password\r"
        expect "# "
    }
}

# Commands to run on server
send "cd /root/auren-production\r"
expect "# "

send "echo 'Restarting services...'\r"
expect "# "

send "docker-compose -f docker-compose.prod.yml restart nginx auren-api\r"
expect "# "

send "sleep 5\r"
expect "# "

send "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'nginx|auren-api'\r"
expect "# "

send "echo 'Testing endpoints...'\r"
expect "# "

send "curl -s http://localhost/api/health | grep -o healthy || echo 'API not ready'\r"
expect "# "

send "echo 'Services restarted!'\r"
expect "# "

send "exit\r"
expect eof
EOF

chmod +x restart.exp
./restart.exp "$PASSWORD"
rm restart.exp

echo ""
echo "✅ Services restarted!"
echo "🌐 Try accessing http://aupex.ai now"
echo ""
echo "If still not loading:"
echo "1. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)"
echo "2. Try incognito/private mode"
echo "3. Check browser console (F12) for errors" 