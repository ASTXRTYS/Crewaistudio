#!/usr/bin/expect -f

# Debug nginx and API connection

set timeout -1
set password ".HvddX+@6dArsKd"

spawn ssh root@144.126.215.218

expect {
    "*password:*" {
        send "$password\r"
        expect "*#"
    }
}

# Check nginx error logs
send "echo '🔍 Checking nginx error logs...'\r"
expect "*#"

send "tail -20 /var/log/nginx/error.log\r"
expect "*#"

# Check if API is actually running
send "echo '🔍 Checking API container...'\r"
expect "*#"

send "docker ps | grep auren-api\r"
expect "*#"

# Test direct API access
send "echo '🔍 Testing direct API access...'\r"
expect "*#"

send "curl -v http://localhost:8080/health 2>&1 | head -20\r"
expect "*#"

# Check container logs
send "echo '🔍 Checking API container logs...'\r"
expect "*#"

send "docker logs auren-api --tail 20\r"
expect "*#"

send "exit\r"
expect eof

puts "\n✅ Debug complete!" 