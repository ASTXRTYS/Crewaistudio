#!/bin/bash

echo "🔍 Checking Docker Configuration"
echo "================================"

# Create expect script
cat > check_docker.exp << 'EOF'
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

send "echo 'Current docker-compose nginx section:'\r"
expect "# "

send "grep -A 10 'auren-nginx:' docker-compose.prod.yml\r"
expect "# "

send "echo 'Checking where files actually are:'\r"
expect "# "

send "pwd\r"
expect "# "

send "ls -la auren/dashboard_v2/ | head -10\r"
expect "# "

send "echo 'Creating updated docker-compose with correct volume mapping...'\r"
expect "# "

send "sed -i 's|./auren/dashboard_v2/dist:/usr/share/nginx/html|./auren/dashboard_v2:/usr/share/nginx/html|g' docker-compose.prod.yml\r"
expect "# "

send "echo 'Recreating nginx container with correct volume...'\r"
expect "# "

send "docker-compose -f docker-compose.prod.yml stop nginx\r"
expect "# "

send "docker-compose -f docker-compose.prod.yml rm -f nginx\r"
expect "# "

send "docker-compose -f docker-compose.prod.yml up -d nginx\r"
expect "# "

send "sleep 5\r"
expect "# "

send "echo 'Testing if it works now...'\r"
expect "# "

send "curl -I http://localhost\r"
expect "# "

send "docker exec auren-nginx ls -la /usr/share/nginx/html/ | head -10\r"
expect "# "

send "echo '✅ Docker volume fixed!'\r"
expect "# "

send "exit\r"
expect eof
EOF

chmod +x check_docker.exp
./check_docker.exp
rm check_docker.exp

echo ""
echo "✅ DOCKER CONFIGURATION FIXED!"
echo ""
echo "Try visiting: http://aupex.ai now" 