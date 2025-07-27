#!/bin/bash

echo "=== AUREN Server Security Audit ==="
echo "Server: 144.126.215.218"
echo "Date: $(date)"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\n${YELLOW}1. Checking Open Ports:${NC}"
echo "Expected: Only 22 (SSH), 80 (HTTP), 443 (HTTPS) should be open externally"
echo "----------------------------------------"
ssh root@144.126.215.218 << 'EOF'
echo "External ports (from netstat):"
netstat -tlnp | grep LISTEN | grep -v "127.0.0.1" | grep -v "::1"
echo ""
echo "UFW Status:"
ufw status numbered
EOF

echo -e "\n${YELLOW}2. Checking Docker Exposed Ports:${NC}"
echo "Verifying no internal services are exposed externally"
echo "----------------------------------------"
ssh root@144.126.215.218 << 'EOF'
echo "Docker port mappings:"
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "0\.0\.0\.0:|::::"
EOF

echo -e "\n${YELLOW}3. Checking SSL/TLS Configuration:${NC}"
echo "----------------------------------------"
ssh root@144.126.215.218 << 'EOF'
echo "Nginx SSL configuration:"
grep -E "ssl_protocols|ssl_ciphers|ssl_prefer_server_ciphers" /etc/nginx/sites-available/* 2>/dev/null || echo "No SSL config found in sites-available"
echo ""
echo "Let's Encrypt certificates:"
ls -la /etc/letsencrypt/live/ 2>/dev/null || echo "No Let's Encrypt certificates found"
EOF

echo -e "\n${YELLOW}4. Checking HIPAA/PHI Security Requirements:${NC}"
echo "----------------------------------------"
ssh root@144.126.215.218 << 'EOF'
echo "Checking for encryption at rest (PostgreSQL):"
docker exec auren-postgres psql -U auren_user -d auren_db -c "SELECT proname FROM pg_proc WHERE proname LIKE '%encrypt%' OR proname LIKE '%decrypt%';" 2>/dev/null || echo "Could not check encryption functions"
echo ""
echo "Checking audit logging:"
docker logs auren-postgres 2>&1 | grep -i "audit" | tail -5 || echo "No audit logs found"
EOF

echo -e "\n${YELLOW}5. Checking Authentication Security:${NC}"
echo "----------------------------------------"
ssh root@144.126.215.218 << 'EOF'
echo "SSH configuration:"
grep -E "PasswordAuthentication|PermitRootLogin|PubkeyAuthentication" /etc/ssh/sshd_config | grep -v "^#"
echo ""
echo "Fail2ban status:"
systemctl is-active fail2ban || echo "fail2ban is not active"
EOF

echo -e "\n${YELLOW}6. Security Recommendations:${NC}"
echo "----------------------------------------"
echo -e "${RED}CRITICAL:${NC}"
echo "1. Disable password authentication for SSH (use keys only)"
echo "2. Install and configure fail2ban to prevent brute force attacks"
echo "3. Close unnecessary ports (5432, 6379, 8000, 8080, 8081 should NOT be publicly accessible)"
echo "4. Configure SSL/TLS properly with Let's Encrypt"
echo "5. Enable firewall rules to restrict access"
echo ""
echo -e "${YELLOW}IMPORTANT:${NC}"
echo "1. Set up automated security updates"
echo "2. Configure log rotation and monitoring"
echo "3. Implement intrusion detection (AIDE or similar)"
echo "4. Regular security audits"
echo ""
echo -e "${GREEN}RECOMMENDED:${NC}"
echo "1. Set up VPN for admin access"
echo "2. Implement rate limiting in Nginx"
echo "3. Configure DDoS protection (Cloudflare)"
echo "4. Set up monitoring alerts"

echo -e "\n${YELLOW}Quick Fix Script Available:${NC}"
echo "Run ./secure_auren_server.sh to implement critical security fixes" 