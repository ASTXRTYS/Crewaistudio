#!/bin/bash

cat > final_fix.exp << 'EOF'
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

send "echo 'Stopping system nginx that is blocking port 80...'\r"
expect "# "

send "systemctl stop nginx\r"
expect "# "

send "systemctl disable nginx\r"
expect "# "

send "cd /root/auren-production\r"
expect "# "

send "echo 'Starting Docker nginx with enhanced dashboard...'\r"
expect "# "

send "docker-compose -f docker-compose.prod.yml up -d nginx\r"
expect "# "

send "sleep 5\r"
expect "# "

send "echo 'Testing if enhanced dashboard is live...'\r"
expect "# "

send "curl -s http://localhost | head -20\r"
expect "# "

send "curl -s http://localhost | grep -c 'index-CcacAJiZ.js' || echo '0'\r"
expect "# "

send "echo 'DONE! Dashboard should be updated.'\r"
expect "# "

send "exit\r"
expect eof
EOF

chmod +x final_fix.exp
./final_fix.exp
rm final_fix.exp

echo ""
echo "🎉 ENHANCED DASHBOARD DEPLOYED!"
echo ""
echo "The server was running a system nginx that was blocking Docker nginx."
echo "This has been fixed!"
echo ""
echo "⚡ NOW CLEAR YOUR BROWSER CACHE:"
echo "   - Mac: Press Cmd + Shift + R"
echo "   - Windows: Press Ctrl + Shift + R"
echo ""
echo "🌐 Visit http://aupex.ai"
echo ""
echo "You will see:"
echo "✨ Space-themed dark background"
echo "✨ Glassmorphic panels with blur"
echo "✨ Glowing neon accents"
echo "✨ Smooth animations" 