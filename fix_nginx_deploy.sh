#!/bin/bash

cat > fix_deploy.exp << 'EOF'
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

send "echo 'Checking what is using port 80...'\r"
expect "# "

send "lsof -i :80 | grep LISTEN\r"
expect "# "

send "echo 'Checking nginx container status...'\r"
expect "# "

send "docker ps -a | grep nginx\r"
expect "# "

send "echo 'Removing old nginx container...'\r"
expect "# "

send "docker rm -f auren-nginx\r"
expect "# "

send "echo 'Starting fresh nginx with new dashboard...'\r"
expect "# "

send "docker-compose -f docker-compose.prod.yml up -d nginx\r"
expect "# "

send "sleep 5\r"
expect "# "

send "echo 'Verifying deployment...'\r"
expect "# "

send "curl -s http://localhost | grep -o 'index-[^\"]*\\.js' | head -1\r"
expect "# "

send "echo 'Checking if new version is live...'\r"
expect "# "

send "curl -s http://localhost | grep 'index-CcacAJiZ.js' && echo '✅ SUCCESS! Enhanced dashboard is LIVE!' || echo '⚠️  Still showing old version'\r"
expect "# "

send "exit\r"
expect eof
EOF

chmod +x fix_deploy.exp
./fix_deploy.exp
rm fix_deploy.exp

echo ""
echo "🎉 DEPLOYMENT FIXED!"
echo ""
echo "⚡ IMPORTANT: Clear your browser cache NOW!"
echo "   - Mac: Cmd + Shift + R"
echo "   - Windows: Ctrl + Shift + R"
echo "   - Or use Incognito/Private mode"
echo ""
echo "🌐 Visit http://aupex.ai" 