# SECURITY RUNBOOK

**Version**: 1.0  
**Last Updated**: January 20, 2025  
**Author**: AUREN Security Team  
**Review Cycle**: Monthly  
**Classification**: CONFIDENTIAL  

---

## 🔒 Executive Summary

This runbook provides security procedures for AUREN infrastructure, including incident response, access management, and preventive measures. Follow these procedures to maintain system security.

**Security Priorities:**
1. Protect user data (PHI/PII)
2. Maintain service availability
3. Preserve audit trail
4. Prevent unauthorized access
5. Ensure compliance

---

## 🚨 Incident Response Procedures

### Security Incident Classification

| Level | Type | Response Time | Examples |
|-------|------|---------------|----------|
| **P1 - Critical** | Active breach | < 15 min | Data exfiltration, ransomware |
| **P2 - High** | Attempted breach | < 1 hour | Brute force attacks, SQL injection |
| **P3 - Medium** | Suspicious activity | < 4 hours | Port scans, unusual patterns |
| **P4 - Low** | Policy violation | < 24 hours | Weak passwords, missing updates |

### Immediate Response Checklist

#### For ANY Security Incident:
1. [ ] **ASSESS** - Determine severity and scope
2. [ ] **CONTAIN** - Isolate affected systems
3. [ ] **NOTIFY** - Alert security team
4. [ ] **PRESERVE** - Capture evidence
5. [ ] **REMEDIATE** - Fix vulnerability
6. [ ] **RECOVER** - Restore services
7. [ ] **DOCUMENT** - Complete incident report

---

## 🔐 Access Management

### SSH Key Management

#### Add New SSH Key
```bash
# On server
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add public key
echo "ssh-rsa AAAAB3... user@host" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Test access
ssh -i private_key root@144.126.215.218
```

#### Revoke SSH Access
```bash
# Remove specific key
sed -i '/user@host/d' ~/.ssh/authorized_keys

# Or edit manually
nano ~/.ssh/authorized_keys
# Delete the line with revoked key

# Force disconnect active sessions
who | grep username
pkill -f "sshd.*username"
```

### Service Account Management

#### Database User Security
```sql
-- Create restricted user
CREATE USER 'app_readonly' WITH PASSWORD 'strong_password_here';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;

-- Revoke permissions
REVOKE ALL ON DATABASE auren_db FROM suspicious_user;
DROP USER IF EXISTS suspicious_user;

-- Audit current users
SELECT usename, usesuper, usecreatedb FROM pg_user;
```

#### API Key Rotation
```bash
# Generate new API key
openssl rand -hex 32

# Update .env file
nano /root/auren-production/.env
# Change: OPENAI_API_KEY=new_key_here

# Restart services
docker-compose -f docker-compose.prod.yml restart auren-api
```

---

## 🛡️ Security Audit Procedures

### Daily Security Checks

```bash
#!/bin/bash
# daily_security_check.sh

echo "=== Daily Security Audit ==="
date

# Check for unauthorized SSH keys
echo -e "\n[SSH Keys]"
cat ~/.ssh/authorized_keys | wc -l

# Check failed login attempts
echo -e "\n[Failed Logins]"
grep "Failed password" /var/log/auth.log | tail -10

# Check open ports
echo -e "\n[Open Ports]"
netstat -tulpn | grep LISTEN

# Check running processes
echo -e "\n[Suspicious Processes]"
ps aux | grep -E "(nc|ncat|perl|python)" | grep -v docker

# Check file changes
echo -e "\n[Recent File Changes]"
find /root -type f -mtime -1 -ls | grep -v "/var/log"

# Check Docker images
echo -e "\n[Docker Images]"
docker images --digests

echo -e "\n=== Audit Complete ==="
```

### Weekly Security Review

#### 1. System Updates
```bash
# Check for security updates
apt update
apt list --upgradable | grep -i security

# Apply security patches only
apt-get install --only-upgrade $(apt list --upgradable 2>/dev/null | grep -i security | cut -d/ -f1)
```

#### 2. Log Analysis
```bash
# SSH access patterns
grep "Accepted publickey" /var/log/auth.log | awk '{print $11}' | sort | uniq -c

# API access patterns
docker logs auren-nginx | grep -E "POST|PUT|DELETE" | awk '{print $1}' | sort | uniq -c

# Database connections
docker exec auren-postgres psql -U auren_user -d auren_db -c "SELECT client_addr, count(*) FROM pg_stat_activity GROUP BY client_addr;"
```

#### 3. Vulnerability Scanning
```bash
# Install scanner
apt install lynis -y

# Run security audit
lynis audit system

# Check Docker security
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image auren-api:latest
```

---

## 🔍 Threat Detection

### Common Attack Patterns

#### 1. Brute Force SSH
```bash
# Detect attempts
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -nr | head -10

# Block attacker
ufw deny from [ATTACKER_IP]

# Enable fail2ban
systemctl status fail2ban
fail2ban-client status sshd
```

#### 2. SQL Injection Attempts
```bash
# Check logs for SQL injection patterns
docker logs auren-nginx | grep -iE "(union.*select|or.*1=1|';|--)"

# Check API logs
docker logs auren-api | grep -iE "(select.*from|drop.*table|insert.*into)"
```

#### 3. Port Scanning
```bash
# Check for port scans
grep "PortScan" /var/log/syslog

# Monitor connections
watch -n 1 'netstat -an | grep SYN_RECV | wc -l'

# Block scanner
iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j RETURN
```

### Real-time Monitoring

```bash
#!/bin/bash
# security_monitor.sh

while true; do
  clear
  echo "=== Security Monitor ==="
  
  # Active connections
  echo -e "\n[Active SSH Sessions]"
  who
  
  # Recent auth failures
  echo -e "\n[Recent Auth Failures]"
  tail -5 /var/log/auth.log | grep -i "failed\|invalid"
  
  # Suspicious network activity
  echo -e "\n[Network Connections]"
  netstat -tn | grep ESTABLISHED | grep -v "127.0.0.1" | awk '{print $5}' | cut -d: -f1 | sort | uniq -c
  
  # Docker activity
  echo -e "\n[Docker Events]"
  docker events --since 30s --until 0s
  
  sleep 30
done
```

---

## 🔒 Secret Management

### Environment Variables

#### Secure .env File
```bash
# Set restrictive permissions
chmod 600 /root/auren-production/.env
chown root:root /root/auren-production/.env

# Encrypt sensitive values
# Install gnupg
apt install gnupg -y

# Encrypt file
gpg -c .env
# Creates .env.gpg

# Decrypt when needed
gpg -d .env.gpg > .env
```

#### Rotate Secrets
```bash
#!/bin/bash
# rotate_secrets.sh

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d)

# Generate new secrets
NEW_JWT_SECRET=$(openssl rand -hex 32)
NEW_DB_PASSWORD=$(openssl rand -base64 32)

# Update .env
sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$NEW_JWT_SECRET/" .env

# Update database password
docker exec auren-postgres psql -U postgres -c "ALTER USER auren_user WITH PASSWORD '$NEW_DB_PASSWORD';"

# Update .env with new DB password
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_DB_PASSWORD/" .env

# Restart services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

echo "Secrets rotated successfully"
```

### SSL/TLS Certificate Management

#### TLS 1.3 Configuration (HIPAA Compliant)
```bash
# Nginx TLS 1.3 configuration
ssl_protocols TLSv1.3;
ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256';
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;

# Security headers for PHI protection
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline';" always;

# PHI-specific headers
add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0" always;
add_header Pragma "no-cache" always;
add_header Expires "0" always;
```

#### Generate Self-Signed Certificate (Temporary)
```bash
# Create certificate with stronger key
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout /etc/ssl/private/aupex.key \
  -out /etc/ssl/certs/aupex.crt \
  -subj "/C=US/ST=State/L=City/O=AUREN/CN=aupex.ai"

# Set permissions
chmod 600 /etc/ssl/private/aupex.key
chmod 644 /etc/ssl/certs/aupex.crt
```

#### Let's Encrypt Setup
```bash
# Install certbot
apt install certbot python3-certbot-nginx -y

# Obtain certificate
certbot --nginx -d aupex.ai -d www.aupex.ai --non-interactive --agree-tos -m admin@aupex.ai

# Auto-renewal
certbot renew --dry-run
```

---

## 🔐 AES-256 Encryption at Rest (PHI Compliance)

### Database-Level Encryption

#### Encryption Functions Setup
```sql
-- Verify pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create master encryption key (use external KMS in production)
INSERT INTO encryption_keys (key_id, encrypted_key) 
VALUES ('default_key', encode(gen_random_bytes(32), 'base64'));

-- Test encryption
SELECT encrypt_phi('sensitive_biometric_data', 'default_key');
SELECT decrypt_phi(encrypt_phi('test_data', 'default_key'), 'default_key');
```

#### PHI Data Encryption Process
```bash
# Encrypt existing biometric data
docker exec -it auren-postgres psql -U auren_user -d auren_db <<EOF
BEGIN;
-- Migrate unencrypted data to encrypted storage
INSERT INTO encrypted_biometric_data (user_id, encrypted_data, key_id, data_type)
SELECT 
    user_id,
    encrypt_phi(raw_data::text, 'default_key'),
    'default_key',
    'biometric_raw'
FROM biometric_events
WHERE created_at > NOW() - INTERVAL '30 days';
COMMIT;
EOF
```

#### Audit Trail for PHI Access
```sql
-- Verify PHI access logging
SELECT * FROM phi_access_log 
WHERE access_time > NOW() - INTERVAL '1 hour'
ORDER BY access_time DESC;

-- Generate compliance report
SELECT 
    date_trunc('day', access_time) as access_date,
    COUNT(*) as access_count,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT accessor_id) as unique_accessors
FROM phi_access_log
WHERE access_time > NOW() - INTERVAL '7 days'
GROUP BY access_date
ORDER BY access_date DESC;
```

#### Key Rotation Procedures
```bash
#!/bin/bash
# rotate_encryption_keys.sh

# Generate new key
NEW_KEY=$(openssl rand -base64 32)
NEW_KEY_ID="key_$(date +%Y%m%d_%H%M%S)"

# Add new key to database
docker exec -it auren-postgres psql -U auren_user -d auren_db <<EOF
INSERT INTO encryption_keys (key_id, encrypted_key) 
VALUES ('$NEW_KEY_ID', '$NEW_KEY');
EOF

# Re-encrypt data with new key (implement gradual migration)
echo "Key rotation initiated. Implement gradual data re-encryption."
```

---

## 🚫 Firewall Configuration

### UFW Rules

```bash
# Current configuration
ufw status verbose

# Basic rules
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS

# Service-specific rules
ufw allow from 172.18.0.0/16 to any port 5432  # PostgreSQL (Docker network only)
ufw allow from 172.18.0.0/16 to any port 6379  # Redis (Docker network only)

# Apply rules
ufw --force enable
```

### Advanced Firewall Rules

```bash
# Rate limiting
ufw limit ssh/tcp

# Country blocking (requires geoip)
# Block specific country
iptables -A INPUT -m geoip --src-cc CN,RU,KP -j DROP

# DDoS protection
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
```

---

## 📝 Compliance Checklist

### HIPAA Security Requirements

#### Administrative Safeguards
- [ ] Security Officer designated
- [ ] Workforce training completed
- [ ] Access management procedures
- [ ] Security incident procedures
- [ ] Business Associate Agreements

#### Physical Safeguards
- [ ] Facility access controls (N/A - cloud)
- [ ] Workstation security
- [ ] Device and media controls

#### Technical Safeguards
- [x] Access control (unique user identification)
- [x] Audit logs and monitoring
- [x] Integrity controls (backups)
- [x] Transmission security (TLS 1.3)
- [x] Encryption at rest (AES-256)

### Security Controls Audit

```bash
# Check encryption status
docker exec auren-postgres psql -U auren_user -d auren_db -c "\df encrypt_phi"

# Verify audit logging
docker exec auren-postgres psql -U auren_user -d auren_db -c "SELECT COUNT(*) FROM audit_logs WHERE created_at > NOW() - INTERVAL '1 day';"

# Check TLS configuration
openssl s_client -connect aupex.ai:443 -tls1_3

# Verify TLS 1.3 is enforced
nmap --script ssl-enum-ciphers -p 443 aupex.ai

# Verify backup encryption
ls -la /root/backups/*.gpg
```

---

## 🚨 Breach Response Procedures

### Immediate Actions (First 30 Minutes)

1. **Isolate Systems**
```bash
# Block all traffic except SSH
ufw --force reset
ufw default deny incoming
ufw default deny outgoing
ufw allow 22/tcp
ufw --force enable

# Stop services
docker-compose -f docker-compose.prod.yml down
```

2. **Preserve Evidence**
```bash
# Create evidence directory
mkdir -p /root/incident-$(date +%Y%m%d-%H%M%S)
cd /root/incident-*

# Capture system state
ps aux > processes.txt
netstat -an > connections.txt
docker ps -a > docker-containers.txt
docker logs --since 48h auren-api > api-logs.txt
docker logs --since 48h auren-nginx > nginx-logs.txt

# Copy logs
cp -r /var/log ./system-logs
tar -czf evidence.tar.gz .
```

3. **Notify Stakeholders**
- Technical team
- Management
- Legal counsel (if PHI involved)
- Affected users (if required)

### Investigation Phase

```bash
# Timeline analysis
grep -h "ERROR\|WARN\|Failed\|Unauthorized" /var/log/*.log | sort -k1,2

# Check for persistence mechanisms
crontab -l
ls -la /etc/cron.*
systemctl list-timers

# Review user accounts
cat /etc/passwd | grep -v nologin
last -20

# Check for backdoors
find / -name "*.php" -type f -exec grep -l "eval\|base64_decode\|system\|exec" {} \;
```

### Recovery Phase

1. **Clean System**
```bash
# Remove suspicious files
rm -rf /tmp/suspicious_file

# Reset all passwords
./rotate_secrets.sh

# Rebuild containers
docker system prune -af
docker-compose -f docker-compose.prod.yml build --no-cache
```

2. **Restore Services**
```bash
# Restore from clean backup
cd /root/auren-production
tar -xzf /root/backups/clean-backup.tar.gz

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify integrity
./health_check.sh
```

---

## 📊 Security Metrics

### Key Security Indicators

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Failed login attempts | < 10/hour | > 50/hour |
| Unauthorized API calls | 0 | > 5/hour |
| Open ports | 4 (22,80,443,8081) | Any additional |
| Security patches | 0 pending | > 0 critical |
| Backup age | < 24 hours | > 48 hours |

### Monthly Security Report Template

```markdown
## Security Report - [MONTH YEAR]

### Summary
- **Incidents**: [Number]
- **Vulnerabilities Found**: [Number]
- **Patches Applied**: [Number]
- **Access Reviews**: [Completed/Pending]

### Incident Details
[List any security incidents]

### Vulnerability Assessment
[Results of security scans]

### Compliance Status
- [ ] HIPAA requirements met
- [ ] Access logs reviewed
- [ ] Backups tested
- [ ] Disaster recovery tested

### Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

**Prepared by**: [Name]
**Reviewed by**: [Name]
```

---

## 🔮 Security Hardening Roadmap

### Immediate (This Week)
1. Enable HTTPS with Let's Encrypt
2. Implement rate limiting
3. Enable fail2ban
4. Complete secret rotation

### Short Term (This Month)
1. Implement WAF (Web Application Firewall)
2. Enable database encryption at rest
3. Set up IDS/IPS
4. Implement 2FA for SSH

### Long Term (This Quarter)
1. Achieve SOC 2 compliance
2. Implement zero-trust architecture
3. Deploy security orchestration
4. Complete HIPAA certification

---

*Security is not a one-time task but a continuous process. Stay vigilant, keep learning, and always assume breach.* 