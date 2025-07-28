#!/bin/bash

echo "🚀 Deploying New AUREN Website"
echo "=============================="

# Package the website
echo "📦 Creating deployment package..."
cd auren/dashboard_v2
tar -czf ../../auren-website.tar.gz .

cd ../..

# Create expect script
cat > deploy_website.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 300
set password ".HvddX+@6dArsKd"

spawn scp auren-website.tar.gz root@144.126.215.218:/root/
expect {
    "password:" {
        send "$password\r"
        exp_continue
    }
    "100%" {
        puts "\n✅ Website uploaded!"
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

send "echo 'Extracting new website...'\r"
expect "# "

send "rm -rf auren/dashboard_v2/*\r"
expect "# "

send "mkdir -p auren/dashboard_v2\r"
expect "# "

send "tar -xzf /root/auren-website.tar.gz -C auren/dashboard_v2/\r"
expect "# "

send "echo 'Starting nginx...'\r"
expect "# "

send "docker-compose -f docker-compose.prod.yml up -d nginx\r"
expect "# "

send "echo '✅ Website deployed!'\r"
expect "# "

send "exit\r"
expect eof
EOF

chmod +x deploy_website.exp
./deploy_website.exp
rm deploy_website.exp

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "Visit: http://aupex.ai"
echo ""
echo "Pages available:"
echo "- Home: http://aupex.ai/"
echo "- Neuroscientist: http://aupex.ai/agents/neuroscientist.html" 