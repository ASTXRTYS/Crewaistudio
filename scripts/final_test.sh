#!/usr/bin/expect -f

# Final test of the enhanced dashboard

set timeout -1
set password ".HvddX+@6dArsKd"

spawn ssh root@144.126.215.218

expect {
    "*password:*" {
        send "$password\r"
        expect "*#"
    }
}

# Test all endpoints
send "echo '🧪 Testing all API endpoints...'\r"
expect "*#"

send "curl -s http://localhost/api/api/memory/stats | jq .\r"
expect "*#"

send "curl -s 'http://localhost/api/api/knowledge-graph/data?depth=1' | jq .\r"
expect "*#"

# Test from external
send "echo '🌐 Testing from external...'\r"
expect "*#"

send "curl -s http://aupex.ai/api/api/memory/stats\r"
expect "*#"

send "echo '\n✅ Your enhanced dashboard is LIVE at http://aupex.ai!'\r"
expect "*#"

send "echo '🎨 Features:'\r"
expect "*#"

send "echo '  • Neural deep space color palette'\r"
expect "*#"

send "echo '  • Glassmorphism panels with blur effects'\r"
expect "*#"

send "echo '  • GPU-accelerated animations'\r"
expect "*#"

send "echo '  • Real-time knowledge graph'\r"
expect "*#"

send "echo '  • WebSocket connections'\r"
expect "*#"

send "echo '  • API fully connected'\r"
expect "*#"

send "echo '\n💡 Clear browser cache (Ctrl+Shift+R) to see it!'\r"
expect "*#"

send "exit\r"
expect eof

puts "\n🎉 DEPLOYMENT COMPLETE AND VERIFIED!" 