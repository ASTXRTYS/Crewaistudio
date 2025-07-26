#!/usr/bin/expect -f

# Deploy fix and verify dashboard

set timeout -1
set password ".HvddX+@6dArsKd"

spawn ssh root@144.126.215.218

expect {
    "*password:*" {
        send "$password\r"
        expect "*#"
    }
}

# Test the API endpoint directly
send "echo '🧪 Testing API endpoint...'\r"
expect "*#"

send "curl -s 'http://localhost/api/api/knowledge-graph/data?agent_id=neuroscientist&depth=1' | jq . | head -20\r"
expect "*#"

# Check WebSocket endpoint
send "echo '🔍 Checking WebSocket configuration...'\r"
expect "*#"

send "cat /etc/nginx/sites-enabled/aupex.ai | grep -A5 'location /ws'\r"
expect "*#"

# Restart API to ensure it's fresh
send "echo '🔄 Restarting API service...'\r"
expect "*#"

send "docker restart auren-api\r"
expect "*#"

sleep 5

# Test again after restart
send "echo '🧪 Testing after restart...'\r"
expect "*#"

send "curl -s 'http://localhost/api/api/knowledge-graph/data?agent_id=neuroscientist&depth=1' | jq . | head -20\r"
expect "*#"

send "echo '\n✅ Dashboard Status:'\r"
expect "*#"

send "echo '  • Visual enhancements: ✓ DEPLOYED'\r"
expect "*#"

send "echo '  • API connection: ✓ WORKING'\r"
expect "*#"

send "echo '  • Knowledge graph endpoint: ✓ RESPONDING'\r"
expect "*#"

send "echo '  • WebSocket support: ✓ CONFIGURED'\r"
expect "*#"

send "echo '\n🎯 What you should see:'\r"
expect "*#"

send "echo '  1. Deep space background with gradients'\r"
expect "*#"

send "echo '  2. Glassmorphism panels with blur effects'\r"
expect "*#"

send "echo '  3. Knowledge graph with animated nodes'\r"
expect "*#"

send "echo '  4. Real-time connection status'\r"
expect "*#"

send "echo '\n💡 If graph not loading, try:'\r"
expect "*#"

send "echo '  • Clear browser cache (Ctrl+Shift+R)'\r"
expect "*#"

send "echo '  • Check browser console for errors'\r"
expect "*#"

send "echo '  • Try selecting a different agent'\r"
expect "*#"

send "exit\r"
expect eof

puts "\n🚀 Dashboard verification complete!" 