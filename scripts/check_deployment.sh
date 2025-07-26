#!/usr/bin/expect -f

# Check what dashboard is actually deployed

set timeout -1
set password ".HvddX+@6dArsKd"

spawn ssh root@144.126.215.218

expect {
    "*password:*" {
        send "$password\r"
        expect "*#"
    }
}

# Check what's in the nginx html directory
send "echo '=== Checking deployed dashboard files ==='\r"
expect "*#"

send "ls -la /usr/share/nginx/html/\r"
expect "*#"

# Check if it's the old or new dashboard
send "echo '=== Checking index.html content ==='\r"
expect "*#"

send "head -20 /usr/share/nginx/html/index.html\r"
expect "*#"

# Check for the CSS file
send "echo '=== Checking for enhanced CSS ==='\r"
expect "*#"

send "ls -la /usr/share/nginx/html/assets/\r"
expect "*#"

# Check if API is actually running
send "echo '=== Checking API status ==='\r"
expect "*#"

send "docker ps | grep auren-api\r"
expect "*#"

send "curl -s http://localhost:8080/health\r"
expect "*#"

# Check nginx config
send "echo '=== Checking nginx config ==='\r"
expect "*#"

send "cat /etc/nginx/sites-available/aupex.ai | grep -A5 'location /api/'\r"
expect "*#"

send "exit\r"
expect eof

puts "\n✅ Deployment check complete!" 