#!/usr/bin/expect -f

# Verify Quick Wins Deployment

set timeout -1
set password ".HvddX+@6dArsKd"

puts "🔍 Verifying Quick Wins Deployment on DigitalOcean..."

spawn ssh root@144.126.215.218

expect {
    "*password:*" {
        send "$password\r"
        expect "*#"
    }
}

# Check services
send "echo '📊 Checking deployed services...'\r"
expect "*#"

send "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'auren|kafka|zookeeper|timescale|STATUS'\r"
expect "*#"

# Check TimescaleDB
send "echo '\r"
expect "*#"

send "echo '1️⃣ TimescaleDB Status:'\r"
expect "*#"

send "docker exec auren-postgres psql -U auren_user -d auren_db -c \"SELECT default_version, installed_version FROM pg_available_extensions WHERE name = 'timescaledb';\" 2>/dev/null || echo 'TimescaleDB not yet installed'\r"
expect "*#"

# Check Kafka
send "echo '\r"
expect "*#"

send "echo '2️⃣ Kafka Status:'\r"
expect "*#"

send "docker logs auren-kafka --tail 5 2>&1 | grep -i 'started' || echo 'Kafka not running'\r"
expect "*#"

# Check TLS/Nginx
send "echo '\r"
expect "*#"

send "echo '3️⃣ TLS 1.3 Status:'\r"
expect "*#"

send "grep -i 'tlsv1.3' /etc/nginx/sites-available/aupex.ai 2>/dev/null && echo 'TLS 1.3 configured!' || echo 'TLS 1.3 not configured'\r"
expect "*#"

# Check API
send "echo '\r"
expect "*#"

send "echo '4️⃣ API Health:'\r"
expect "*#"

send "curl -s http://localhost:8080/health | jq . || echo 'API not responding'\r"
expect "*#"

# Check ports
send "echo '\r"
expect "*#"

send "echo '5️⃣ Open Ports:'\r"
expect "*#"

send "ufw status | grep -E '9092|8081' || echo 'Kafka ports not open'\r"
expect "*#"

send "exit\r"
expect eof

puts "\n✅ Verification complete!" 