# DISASTER RECOVERY PLAN

**Version**: 1.0  
**Last Updated**: January 20, 2025  
**Author**: AUREN Infrastructure Team  
**Review Cycle**: Quarterly  

---

## 🚨 Executive Summary

This document provides comprehensive procedures for recovering AUREN services in case of disasters. All procedures have been designed for rapid execution with minimal downtime.

**Recovery Targets:**
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 24 hours
- **MTTR (Mean Time To Recovery)**: 2 hours

---

## 📞 Emergency Contacts

### Primary Contacts
| Role | Name | Phone | Email | Availability |
|------|------|-------|-------|--------------|
| Infrastructure Lead | [Name] | [Phone] | [Email] | 24/7 |
| Backend Lead | [Name] | [Phone] | [Email] | Business hours |
| Database Admin | [Name] | [Phone] | [Email] | 24/7 |
| DigitalOcean Support | N/A | N/A | support@digitalocean.com | 24/7 |

### Escalation Path
1. Infrastructure Lead (0-30 min)
2. Backend Lead (30-60 min)
3. CTO/Technical Director (60+ min)

---

## 🎯 Disaster Scenarios

### 1. Complete Server Failure
**Symptoms**: Server unreachable, all services down  
**Impact**: Total service outage  
**Recovery Time**: 2-4 hours

### 2. Database Corruption
**Symptoms**: API errors, data inconsistencies  
**Impact**: Service degradation or outage  
**Recovery Time**: 1-2 hours

### 3. Docker Service Failures
**Symptoms**: Individual services crashing  
**Impact**: Partial service outage  
**Recovery Time**: 15-30 minutes

### 4. Network/DNS Issues
**Symptoms**: Site unreachable but server running  
**Impact**: User-facing outage  
**Recovery Time**: 15-60 minutes

### 5. Security Breach
**Symptoms**: Unauthorized access, data manipulation  
**Impact**: Data integrity compromise  
**Recovery Time**: 2-8 hours

---

## 🔄 Recovery Procedures

### Scenario 1: Complete Server Failure

#### Step 1: Verify Failure
```bash
# Try multiple connection methods
ping 144.126.215.218
ssh root@144.126.215.218
curl http://aupex.ai

# Check DigitalOcean console
# Login to DigitalOcean → Droplets → Check status
```

#### Step 2: Restore from DigitalOcean Backup
```bash
# From DigitalOcean Console:
1. Go to Droplets → auren-production
2. Click "Backups" tab
3. Select most recent backup
4. Click "Restore Backup"
5. Choose "Restore to new Droplet"
6. Select same size/region
7. Complete restoration

# Update DNS to new IP
# In Cloudflare: Update A record to new IP
```

#### Step 3: Restore Latest Data
```bash
# SSH to new server
ssh root@[NEW_IP]

# Restore database from daily backup
cd /root/backups
gunzip postgres_[LATEST_DATE].sql.gz
docker exec -i auren-postgres psql -U auren_user auren_db < postgres_[LATEST_DATE].sql

# Restore Redis if needed
docker cp redis_[LATEST_DATE].rdb auren-redis:/data/dump.rdb
docker restart auren-redis
```

#### Step 4: Verify Services
```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# Test endpoints
curl http://[NEW_IP]/api/health
curl http://aupex.ai/api/health

# Monitor logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Scenario 2: Database Corruption

#### Step 1: Identify Corruption
```bash
# Check PostgreSQL logs
docker logs auren-postgres --tail 100 | grep ERROR

# Try to connect
docker exec -it auren-postgres psql -U auren_user -d auren_db -c "SELECT 1;"

# Check table integrity
docker exec -it auren-postgres psql -U auren_user -d auren_db -c "\dt"
```

#### Step 2: Stop Affected Services
```bash
# Stop API to prevent further corruption
docker-compose -f docker-compose.prod.yml stop auren-api

# Keep database running for recovery
```

#### Step 3: Restore Database
```bash
# Option A: From backup (data loss up to 24h)
cd /root/backups
gunzip postgres_[LATEST_DATE].sql.gz
docker exec -i auren-postgres psql -U auren_user -c "DROP DATABASE auren_db;"
docker exec -i auren-postgres psql -U auren_user -c "CREATE DATABASE auren_db;"
docker exec -i auren-postgres psql -U auren_user auren_db < postgres_[LATEST_DATE].sql

# Option B: Point-in-time recovery (if WAL archiving enabled)
# Restore to specific timestamp before corruption
```

#### Step 4: Restart Services
```bash
# Start API service
docker-compose -f docker-compose.prod.yml start auren-api

# Verify data integrity
docker exec auren-api python -m auren.scripts.verify_database
```

### Scenario 3: Docker Service Failures

#### Step 1: Identify Failed Service
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check specific service logs
docker logs auren-[SERVICE_NAME] --tail 50

# Check system resources
docker stats --no-stream
df -h
free -m
```

#### Step 2: Restart Failed Service
```bash
# Try gentle restart first
docker-compose -f docker-compose.prod.yml restart [SERVICE_NAME]

# If that fails, recreate container
docker-compose -f docker-compose.prod.yml stop [SERVICE_NAME]
docker-compose -f docker-compose.prod.yml rm -f [SERVICE_NAME]
docker-compose -f docker-compose.prod.yml up -d [SERVICE_NAME]

# If still failing, rebuild
docker-compose -f docker-compose.prod.yml build --no-cache [SERVICE_NAME]
docker-compose -f docker-compose.prod.yml up -d [SERVICE_NAME]
```

#### Step 3: Verify Recovery
```bash
# Check logs
docker logs -f auren-[SERVICE_NAME]

# Test functionality
# For API:
curl http://localhost:8080/health

# For Redis:
docker exec auren-redis redis-cli ping

# For PostgreSQL:
docker exec auren-postgres pg_isready
```

### Scenario 4: Network/DNS Issues

#### Step 1: Diagnose Issue
```bash
# From server
curl http://localhost
curl http://localhost:8080/health
netstat -tulpn | grep :80

# From outside
dig aupex.ai
nslookup aupex.ai
traceroute aupex.ai
```

#### Step 2: Fix DNS Issues
```bash
# Check Cloudflare
# 1. Login to Cloudflare
# 2. Verify A record points to 144.126.215.218
# 3. Check proxy status (should be OFF for now)
# 4. Clear Cloudflare cache if needed

# Check DigitalOcean firewall
# 1. Login to DigitalOcean
# 2. Networking → Firewalls
# 3. Verify ports 80, 443, 22 are open
```

#### Step 3: Fix Local Network Issues
```bash
# Restart networking
systemctl restart networking

# Check UFW firewall
ufw status
ufw allow 80/tcp
ufw allow 443/tcp

# Restart Nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Scenario 5: Security Breach

#### Step 1: Immediate Containment
```bash
# Block attacker IP (if known)
ufw deny from [ATTACKER_IP]

# Disable compromised accounts
# Change all passwords immediately

# Take server offline if severe
docker-compose -f docker-compose.prod.yml down
```

#### Step 2: Assess Damage
```bash
# Check access logs
docker logs auren-nginx | grep -E "POST|PUT|DELETE"
grep "Failed password" /var/log/auth.log

# Check for unauthorized changes
git status
find /root -type f -mtime -1 -ls

# Export audit trail
docker exec auren-postgres pg_dump -U auren_user -t audit_logs auren_db > breach_audit.sql
```

#### Step 3: Recovery
```bash
# Restore from known good backup
# Follow Complete Server Failure procedure

# Rotate all secrets
# Update .env file with new keys
# Update database passwords
# Regenerate API keys

# Implement additional security
# Enable 2FA
# Implement IP whitelisting
# Enable audit logging
```

---

## 📊 Recovery Priority Order

### Service Start Order (Critical Path)
1. **PostgreSQL** - All services depend on database
2. **Redis** - Required for caching and sessions
3. **ChromaDB** - Needed for semantic search
4. **AUREN API** - Core application service
5. **Nginx** - User-facing web server
6. **Kafka/Zookeeper** - Event streaming (if used)
7. **Monitoring** - Observability stack

### Data Recovery Priority
1. **User data** - Critical business data
2. **Configuration** - System settings
3. **Logs** - For debugging/audit
4. **Cache** - Can be regenerated

---

## 🛠️ Recovery Tools

### Backup Locations
```bash
# Local backups
/root/backups/
├── postgres_*.sql.gz    # Daily database backups
├── redis_*.rdb          # Redis snapshots
└── configs_*.tar.gz     # Configuration backups

# DigitalOcean backups
# Weekly full droplet snapshots (4 weeks retention)
# Access via DigitalOcean console → Backups

# Offsite backups (if configured)
# S3/Spaces bucket: s3://auren-backups/
```

### Recovery Scripts
```bash
# Quick recovery script
cat > /root/scripts/quick_recover.sh << 'EOF'
#!/bin/bash
# AUREN Quick Recovery Script

echo "Starting AUREN recovery..."

# Check what's running
docker-compose -f docker-compose.prod.yml ps

# Restart all services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Wait for services
sleep 30

# Verify health
curl http://localhost:8080/health

echo "Recovery complete. Check logs for errors."
EOF

chmod +x /root/scripts/quick_recover.sh
```

### Verification Commands
```bash
# Health check all services
for service in postgres redis chromadb auren-api nginx; do
  echo "Checking $service..."
  docker ps | grep $service && echo "✓ Running" || echo "✗ Not running"
done

# Test all endpoints
curl http://localhost/
curl http://localhost:8080/health
curl http://localhost:8080/api/memory/stats

# Check disk/memory
df -h
free -m
docker stats --no-stream
```

---

## 📋 Post-Recovery Checklist

### Immediate Actions
- [ ] All services running
- [ ] Website accessible
- [ ] API responding
- [ ] Database queries working
- [ ] No error logs
- [ ] Monitoring active

### Within 1 Hour
- [ ] Notify team of recovery
- [ ] Document incident timeline
- [ ] Check data integrity
- [ ] Verify backups working
- [ ] Review security logs

### Within 24 Hours
- [ ] Complete incident report
- [ ] Update runbooks if needed
- [ ] Schedule post-mortem
- [ ] Test backup restoration
- [ ] Implement preventive measures

---

## 📝 Incident Report Template

```markdown
## Incident Report - [DATE]

**Incident Type**: [Server Failure/Database Corruption/etc]
**Start Time**: [HH:MM UTC]
**End Time**: [HH:MM UTC]
**Total Downtime**: [X hours Y minutes]
**Data Loss**: [None/Description]

### Timeline
- HH:MM - Issue detected
- HH:MM - Recovery started
- HH:MM - Service restored
- HH:MM - Full recovery confirmed

### Root Cause
[Description of what caused the incident]

### Actions Taken
1. [Action 1]
2. [Action 2]

### Lessons Learned
- [Learning 1]
- [Learning 2]

### Prevention Measures
- [Measure 1]
- [Measure 2]

**Report By**: [Name]
**Date**: [Date]
```

---

## 🔧 Preventive Measures

### Daily
- Monitor service health
- Check backup completion
- Review error logs

### Weekly
- Test service restart
- Verify backup integrity
- Update system packages

### Monthly
- Full recovery drill
- Security audit
- Capacity review

### Quarterly
- DR plan review
- Update contact list
- Improve procedures

---

## 🚀 Recovery Time Improvements

### Current vs Target
| Scenario | Current | Target | Improvement Needed |
|----------|---------|--------|-------------------|
| Server Failure | 2-4 hrs | 1 hr | Automated provisioning |
| Database Corruption | 1-2 hrs | 30 min | Streaming replication |
| Service Failure | 15-30 min | 5 min | Auto-restart policies |
| Network Issues | 15-60 min | 10 min | Multi-region setup |

### Improvement Roadmap
1. **Implement HA Database** - PostgreSQL replication
2. **Add Load Balancer** - Automatic failover
3. **Multi-Region Setup** - Geographic redundancy
4. **Automated Recovery** - Self-healing systems
5. **Continuous Backups** - Reduce RPO to minutes

---

*Remember: In a disaster, stay calm, follow procedures, and communicate clearly with the team.* 