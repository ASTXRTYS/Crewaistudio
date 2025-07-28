# TROUBLESHOOTING PLAYBOOK

**Version**: 1.0  
**Last Updated**: January 20, 2025  
**Author**: AUREN Support Team  
**Review Cycle**: Monthly  

---

## 🔍 Executive Summary

This playbook provides systematic troubleshooting procedures for common issues in AUREN infrastructure. Follow these guides to quickly diagnose and resolve problems.

**Troubleshooting Priority:**
1. Check service status
2. Review logs
3. Verify resources
4. Test connectivity
5. Apply fix

---

## 🚨 Common Issues & Solutions

### 1. Website Not Loading

#### Symptoms
- Browser shows "Cannot reach site"
- Timeout errors
- 502 Bad Gateway

#### Diagnosis Steps
```bash
# 1. Check if server is reachable
ping 144.126.215.218
curl -I http://aupex.ai

# 2. SSH to server
ssh root@144.126.215.218

# 3. Check Nginx status
docker ps | grep nginx
docker logs auren-nginx --tail 50

# 4. Check API status
docker ps | grep auren-api
curl http://localhost:8080/health
```

#### Solutions
```bash
# Fix 1: Restart Nginx
docker-compose -f docker-compose.prod.yml restart nginx

# Fix 2: Restart entire stack
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Fix 3: Check disk space
df -h
# If full, clean up:
docker system prune -af
```

### 2. API Errors (500 Internal Server Error)

#### Symptoms
- API returns 500 errors
- Slow response times
- Timeout errors

#### Diagnosis Steps
```bash
# 1. Check API logs
docker logs auren-api --tail 100 | grep ERROR

# 2. Check database connection
docker exec auren-api pg_isready -h postgres -U auren_user

# 3. Check Redis connection
docker exec auren-api redis-cli -h redis ping

# 4. Check memory usage
docker stats auren-api --no-stream
```

#### Solutions
```bash
# Fix 1: Restart API service
docker-compose -f docker-compose.prod.yml restart auren-api

# Fix 2: Check environment variables
docker exec auren-api env | grep -E "(DATABASE_URL|REDIS_URL)"

# Fix 3: Increase memory limit
docker update --memory="1g" auren-api
docker restart auren-api

# Fix 4: Check for code errors
docker exec auren-api python -m py_compile /app/auren/api/dashboard_api_minimal.py
```

### 3. Database Connection Failed

#### Symptoms
- "could not connect to database" errors
- psycopg2.OperationalError
- Connection refused

#### Diagnosis Steps
```bash
# 1. Check PostgreSQL status
docker ps | grep postgres
docker logs auren-postgres --tail 50

# 2. Test connection
docker exec -it auren-postgres psql -U auren_user -d auren_db -c "SELECT 1;"

# 3. Check connections
docker exec auren-postgres psql -U auren_user -d auren_db -c "SELECT count(*) FROM pg_stat_activity;"

# 4. Check disk space for database
docker exec auren-postgres df -h /var/lib/postgresql/data
```

#### Solutions
```bash
# Fix 1: Restart PostgreSQL
docker-compose -f docker-compose.prod.yml restart postgres

# Fix 2: Reset connections
docker exec auren-postgres psql -U auren_user -d auren_db -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"

# Fix 3: Increase connection limit
docker exec auren-postgres psql -U postgres -c "ALTER SYSTEM SET max_connections = 200;"
docker-compose -f docker-compose.prod.yml restart postgres

# Fix 4: Fix corrupted indexes
docker exec auren-postgres psql -U auren_user -d auren_db -c "REINDEX DATABASE auren_db;"
```

### 4. Redis Memory Issues

#### Symptoms
- "OOM command not allowed" errors
- Cache misses increasing
- Slow performance

#### Diagnosis Steps
```bash
# 1. Check Redis memory
docker exec auren-redis redis-cli INFO memory

# 2. Check eviction stats
docker exec auren-redis redis-cli INFO stats | grep evicted

# 3. Monitor real-time
docker exec auren-redis redis-cli --stat

# 4. Check key count
docker exec auren-redis redis-cli DBSIZE
```

#### Solutions
```bash
# Fix 1: Clear unnecessary keys
docker exec auren-redis redis-cli FLUSHDB

# Fix 2: Set memory limit with eviction
docker exec auren-redis redis-cli CONFIG SET maxmemory 1gb
docker exec auren-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Fix 3: Restart with more memory
docker update --memory="512m" auren-redis
docker restart auren-redis

# Fix 4: Analyze large keys
docker exec auren-redis redis-cli --bigkeys
```

### 5. Docker Services Not Starting

#### Symptoms
- Container exits immediately
- "Restarting" loop
- Port already in use

#### Diagnosis Steps
```bash
# 1. Check all service status
docker-compose -f docker-compose.prod.yml ps

# 2. Check for port conflicts
netstat -tulpn | grep -E "(80|443|8080|5432|6379)"

# 3. Check Docker daemon
systemctl status docker
journalctl -u docker --tail 50

# 4. Check compose syntax
docker-compose -f docker-compose.prod.yml config
```

#### Solutions
```bash
# Fix 1: Stop conflicting services
systemctl stop apache2  # If Apache is running
systemctl stop nginx    # If system Nginx is running

# Fix 2: Clean up containers
docker-compose -f docker-compose.prod.yml down
docker system prune -af
docker-compose -f docker-compose.prod.yml up -d

# Fix 3: Reset Docker
systemctl restart docker
docker-compose -f docker-compose.prod.yml up -d

# Fix 4: Rebuild specific service
docker-compose -f docker-compose.prod.yml build --no-cache [service-name]
docker-compose -f docker-compose.prod.yml up -d [service-name]
```

### 6. High CPU/Memory Usage

#### Symptoms
- Server slow/unresponsive
- SSH connection sluggish
- Services timing out

#### Diagnosis Steps
```bash
# 1. Check system resources
htop
docker stats

# 2. Find CPU hogs
ps aux | sort -nrk 3,3 | head -10

# 3. Find memory hogs
ps aux | sort -nrk 4,4 | head -10

# 4. Check disk I/O
iotop
```

#### Solutions
```bash
# Fix 1: Restart heavy services
docker-compose -f docker-compose.prod.yml restart [heavy-service]

# Fix 2: Limit container resources
docker update --cpus="0.5" --memory="512m" [container-name]

# Fix 3: Clear system cache
sync && echo 3 > /proc/sys/vm/drop_caches

# Fix 4: Enable swap if not present
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

### 7. Kafka Issues

#### Symptoms
- Messages not processing
- Consumer lag increasing
- Connection refused

#### Diagnosis Steps
```bash
# 1. Check Kafka status
docker ps | grep kafka
docker logs auren-kafka --tail 50

# 2. Check Zookeeper
docker ps | grep zookeeper
docker logs auren-zookeeper --tail 50

# 3. List topics
docker exec auren-kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# 4. Check consumer groups
docker exec auren-kafka kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list
```

#### Solutions
```bash
# Fix 1: Restart Kafka cluster
docker-compose -f docker-compose.prod.yml restart zookeeper
sleep 10
docker-compose -f docker-compose.prod.yml restart kafka

# Fix 2: Reset consumer offset
docker exec auren-kafka kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group [group-name] --reset-offsets --to-earliest --execute --topic [topic-name]

# Fix 3: Increase Kafka memory
docker update --memory="1g" auren-kafka
docker restart auren-kafka

# Fix 4: Clean up old logs
docker exec auren-kafka rm -rf /var/lib/kafka/data/*-delete
```

---

## 🔧 Service-Specific Troubleshooting

### PostgreSQL Issues

#### Check Health
```bash
# Connection test
docker exec auren-postgres pg_isready

# Database size
docker exec auren-postgres psql -U auren_user -d auren_db -c "SELECT pg_database_size('auren_db');"

# Active queries
docker exec auren-postgres psql -U auren_user -d auren_db -c "SELECT pid, age(clock_timestamp(), query_start), usename, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;"

# Kill long-running query
docker exec auren-postgres psql -U auren_user -d auren_db -c "SELECT pg_cancel_backend([PID]);"
```

#### Common Fixes
```bash
# Vacuum database
docker exec auren-postgres vacuumdb -U auren_user -d auren_db -z

# Analyze tables
docker exec auren-postgres psql -U auren_user -d auren_db -c "ANALYZE;"

# Check for locks
docker exec auren-postgres psql -U auren_user -d auren_db -c "SELECT * FROM pg_locks WHERE NOT granted;"
```

### ChromaDB Issues

#### Check Health
```bash
# Test API
curl http://localhost:8000/api/v1/heartbeat

# Check collections
curl http://localhost:8000/api/v1/collections

# Check disk usage
docker exec auren-chromadb df -h /chroma
```

#### Common Fixes
```bash
# Restart service
docker restart auren-chromadb

# Clear corrupted data
docker exec auren-chromadb rm -rf /chroma/chroma.sqlite3-wal
docker restart auren-chromadb

# Rebuild index
# Stop service, delete data, restart
docker stop auren-chromadb
docker rm auren-chromadb
docker volume rm chromadb-data
docker-compose -f docker-compose.prod.yml up -d chromadb
```

### Nginx Issues

#### Check Configuration
```bash
# Test config
docker exec auren-nginx nginx -t

# Reload config
docker exec auren-nginx nginx -s reload

# Check access logs
docker logs auren-nginx --tail 100 | grep -E "(404|500|502|503)"

# Check error logs
docker exec auren-nginx cat /var/log/nginx/error.log
```

#### Common Fixes
```bash
# Fix permissions
docker exec auren-nginx chown -R nginx:nginx /usr/share/nginx/html

# Clear cache
docker exec auren-nginx rm -rf /var/cache/nginx/*

# Increase buffers
# Edit nginx.conf and add:
# client_body_buffer_size 128k;
# client_max_body_size 10m;
# client_header_buffer_size 1k;
```

---

## 📋 Diagnostic Commands Cheatsheet

### System Health
```bash
# Overall health
curl http://aupex.ai/api/health | jq .

# Service status
docker-compose -f docker-compose.prod.yml ps

# Resource usage
docker stats --no-stream

# Disk space
df -h

# Memory
free -m

# Network connections
netstat -an | grep ESTABLISHED | wc -l

# Process list
ps aux --sort=-%cpu | head -10
```

### Logs Analysis
```bash
# All logs
docker-compose -f docker-compose.prod.yml logs --tail=100

# Specific service
docker logs [container-name] --tail=50 -f

# Error grep
docker-compose -f docker-compose.prod.yml logs | grep -i error

# Time range
docker logs --since 2h [container-name]
```

### Performance Checks
```bash
# API response time
time curl http://localhost:8080/health

# Database query time
docker exec auren-postgres psql -U auren_user -d auren_db -c "\timing on" -c "SELECT COUNT(*) FROM events;"

# Redis latency
docker exec auren-redis redis-cli --latency

# Network latency
ping -c 10 aupex.ai
```

---

## 🚑 Emergency Procedures

### System Unresponsive
```bash
# 1. Try to SSH
ssh -o ConnectTimeout=10 root@144.126.215.218

# 2. If SSH works, restart Docker
systemctl restart docker

# 3. If not, use DigitalOcean console
# Power cycle through web interface

# 4. After reboot
cd /root/auren-production
docker-compose -f docker-compose.prod.yml up -d
```

### Data Corruption
```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yml stop

# 2. Backup current state
tar -czf emergency-backup-$(date +%Y%m%d-%H%M%S).tar.gz .

# 3. Restore from backup
cd /root/backups
gunzip postgres_[LATEST].sql.gz
docker exec -i auren-postgres psql -U auren_user auren_db < postgres_[LATEST].sql

# 4. Restart services
docker-compose -f docker-compose.prod.yml up -d
```

### Security Breach
```bash
# 1. Isolate server
ufw default deny incoming
ufw default deny outgoing
ufw allow 22/tcp  # Keep SSH

# 2. Snapshot evidence
docker logs --since 24h > breach-logs.txt
ps aux > breach-processes.txt
netstat -an > breach-connections.txt

# 3. Reset credentials
# Change all passwords in .env
# Regenerate API keys
# Update database passwords

# 4. Rebuild clean
docker-compose -f docker-compose.prod.yml down
docker system prune -af
# Restore from known good backup
```

---

## 📝 Troubleshooting Log Template

```markdown
## Issue Report - [DATE TIME]

### Problem Description
- **Service Affected**: [Service name]
- **Symptoms**: [What's wrong]
- **First Noticed**: [When]
- **Impact**: [Who/what affected]

### Diagnostic Steps Taken
1. [Step 1 and result]
2. [Step 2 and result]
3. [Step 3 and result]

### Root Cause
[What caused the issue]

### Solution Applied
[What fixed it]

### Prevention
[How to prevent recurrence]

**Resolved By**: [Name]
**Time to Resolution**: [X minutes]
```

---

## 🔄 Preventive Maintenance

### Daily Checks
```bash
#!/bin/bash
# daily_health_check.sh

echo "=== Daily Health Check ==="
echo "Date: $(date)"

# Check all services
docker-compose -f docker-compose.prod.yml ps

# Check disk space
df -h | grep -E "(/$|/var)"

# Check memory
free -m

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs --since 24h | grep -i error | wc -l

# Test endpoints
curl -s http://localhost:8080/health || echo "API Health check failed"

echo "=== Check Complete ==="
```

### Weekly Maintenance
1. Review error logs
2. Clean up old logs
3. Update Docker images
4. Test backups
5. Security patches

---

*Remember: Document every issue and solution to improve this playbook continuously.* 