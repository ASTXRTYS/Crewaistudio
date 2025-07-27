#!/bin/bash

echo "🚀 Auto-deploying Enhanced Dashboard"
echo "===================================="

# Create expect script with embedded password
cat > deploy_auto.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 300
set password ".HvddX+@6dArsKd"

# First, upload the file
spawn scp enhanced-dashboard.tar.gz root@144.126.215.218:/root/
expect {
    "password:" {
        send "$password\r"
        exp_continue
    }
    "100%" {
        puts "\n✅ File uploaded successfully!"
    }
    eof
}

# Now SSH and deploy
spawn ssh root@144.126.215.218
expect {
    "password:" {
        send "$password\r"
        expect "# "
    }
}

send "cd /root/auren-production\r"
expect "# "

send "echo '📦 Extracting enhanced dashboard...'\r"
expect "# "

send "tar -xzf /root/enhanced-dashboard.tar.gz -C auren/dashboard_v2/\r"
expect "# "

send "echo '🔄 Restarting nginx...'\r"
expect "# "

send "docker-compose -f docker-compose.prod.yml stop nginx\r"
expect "# "

send "docker-compose -f docker-compose.prod.yml start nginx\r"
expect "# "

send "sleep 5\r"
expect "# "

send "echo '✅ Testing deployment...'\r"
expect "# "

send "curl -s http://localhost | grep 'index-CcacAJiZ.js' && echo '✅ NEW VERSION DEPLOYED!' || echo '❌ Still old version'\r"
expect "# "

send "rm /root/enhanced-dashboard.tar.gz\r"
expect "# "

send "exit\r"
expect eof
EOF

chmod +x deploy_auto.exp
./deploy_auto.exp
rm deploy_auto.exp

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo ""
echo "⚡ NOW CLEAR YOUR BROWSER CACHE:"
echo "   - Mac: Cmd + Shift + R"
echo "   - Windows: Ctrl + Shift + R"
echo ""
echo "🌐 Visit http://aupex.ai"
echo ""
echo "You should see:"
echo "✨ Glassmorphic panels with blur effects"
echo "✨ Space-themed dark background"
echo "✨ Glowing neon accents"
echo "✨ Smooth animations" 