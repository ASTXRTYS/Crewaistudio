#!/bin/bash

echo "🚀 Deploying Enhanced AUREN Dashboard"
echo "====================================="

SERVER_IP="144.126.215.218"
PASSWORD=".HvddX+@6dArsKd"

# Create deployment package
echo "📦 Creating deployment package..."
cd auren/dashboard_v2
tar -czf enhanced-dashboard.tar.gz dist/

# Create expect script for deployment
cat > ../../../deploy.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 300
set password [lindex $argv 0]

spawn scp auren/dashboard_v2/enhanced-dashboard.tar.gz root@144.126.215.218:/root/

expect {
    "password:" {
        send "$password\r"
        exp_continue
    }
    "100%" {
        puts "\nFile uploaded successfully!"
    }
    eof
}

spawn ssh root@144.126.215.218

expect {
    "password:" {
        send "$password\r"
        expect "# "
    }
}

send "cd /root/auren-production\r"
expect "# "

send "echo 'Backing up current dashboard...'\r"
expect "# "

send "cp -r auren/dashboard_v2/dist auren/dashboard_v2/dist.backup\r"
expect "# "

send "echo 'Extracting new dashboard...'\r"
expect "# "

send "tar -xzf /root/enhanced-dashboard.tar.gz -C auren/dashboard_v2/\r"
expect "# "

send "echo 'Restarting services...'\r"
expect "# "

send "docker-compose -f docker-compose.prod.yml restart nginx\r"
expect "# "

send "sleep 3\r"
expect "# "

send "echo 'Testing deployment...'\r"
expect "# "

send "curl -s http://localhost | grep -c 'index-CcacAJiZ.js' || echo 'New version not detected'\r"
expect "# "

send "echo 'Deployment complete!'\r"
expect "# "

send "exit\r"
expect eof
EOF

cd ../../..
chmod +x deploy.exp
./deploy.exp "$PASSWORD"
rm deploy.exp
rm auren/dashboard_v2/enhanced-dashboard.tar.gz

echo ""
echo "✅ Enhanced dashboard deployed!"
echo "🌐 Clear your browser cache and visit http://aupex.ai"
echo ""
echo "Force refresh:"
echo "- Mac: Cmd + Shift + R"
echo "- Windows: Ctrl + Shift + R" 