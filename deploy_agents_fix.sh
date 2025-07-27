#!/bin/bash

echo "🔧 Deploying Agents Page Fix"
echo "============================"

# Create expect script
cat > deploy_agents.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 300
set password ".HvddX+@6dArsKd"

spawn scp auren/dashboard_v2/agents/index.html root@144.126.215.218:/root/
expect {
    "password:" {
        send "$password\r"
        exp_continue
    }
    "100%" {
        puts "\n✅ Agents page uploaded!"
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

send "cp /root/index.html auren/dashboard_v2/agents/\r"
expect "# "

send "echo '✅ Agents page deployed!'\r"
expect "# "

send "exit\r"
expect eof
EOF

chmod +x deploy_agents.exp
./deploy_agents.exp
rm deploy_agents.exp

echo ""
echo "✅ AGENTS PAGE FIXED!"
echo "Visit: http://aupex.ai/agents/" 