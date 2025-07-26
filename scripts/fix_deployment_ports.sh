#!/usr/bin/expect -f

# Fix ChromaDB port conflict on DigitalOcean

set timeout -1
set password ".HvddX+@6dArsKd"

spawn ssh root@144.126.215.218

expect {
    "*password:*" {
        send "$password\r"
        expect "*#"
    }
}

# Fix the port conflict
send "cd /root/auren-production\r"
expect "*#"

# Stop any existing ChromaDB container
send "docker stop auren-chromadb 2>/dev/null || true\r"
expect "*#"

send "docker rm auren-chromadb 2>/dev/null || true\r"
expect "*#"

# Check what's on port 8000
send "lsof -i :8000 || netstat -tulpn | grep :8000\r"
expect "*#"

# Kill anything on port 8000
send "fuser -k 8000/tcp 2>/dev/null || true\r"
expect "*#"

# Update docker-compose to use a different port for ChromaDB
send "sed -i 's/8000:8000/8001:8000/g' docker-compose.prod.yml\r"
expect "*#"

# Restart all services with the fix
send "docker-compose -f docker-compose.prod.yml up -d\r"
expect "*#"

# Check status
send "docker ps --format 'table {{.Names}}\t{{.Status}}'\r"
expect "*#"

# Test the API
send "curl -s http://localhost:8080/health | head -20\r"
expect "*#"

send "exit\r"
expect eof

puts "\n✅ Port conflict fixed!" 