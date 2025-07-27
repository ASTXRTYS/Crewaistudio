#!/bin/bash

echo "🔥 DESTROYING CURRENT DASHBOARD"
echo "================================"

# Create expect script to clean the server
cat > destroy.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 300
set password ".HvddX+@6dArsKd"

spawn ssh root@144.126.215.218
expect {
    "password:" {
        send "$password\r"
        expect "# "
    }
}

send "cd /root/auren-production\r"
expect "# "

send "echo 'Stopping all services...'\r"
expect "# "

send "docker-compose -f docker-compose.prod.yml stop nginx\r"
expect "# "

send "echo 'Removing old dashboard completely...'\r"
expect "# "

send "rm -rf auren/dashboard_v2/dist/*\r"
expect "# "

send "rm -rf auren/dashboard_v2/src/components/*\r"
expect "# "

send "rm -rf auren/dashboard_v2/src/styles/*\r"
expect "# "

send "echo 'Cleaning up old files...'\r"
expect "# "

send "rm -f /root/enhanced-dashboard.tar.gz\r"
expect "# "

send "rm -rf auren/dashboard_v2/dist.backup\r"
expect "# "

send "echo '✅ Old dashboard completely destroyed!'\r"
expect "# "

send "exit\r"
expect eof
EOF

chmod +x destroy.exp
./destroy.exp
rm destroy.exp

echo ""
echo "✅ CURRENT DASHBOARD DESTROYED!"
echo "Ready to build a proper website from scratch" 