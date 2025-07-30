# SOP-001: MASTER OPERATIONS GUIDE - LOCKED CONFIGURATION

**Created**: January 30, 2025
**Status**: ✅ PRODUCTION READY - LOCKED CONFIGURATION
**Critical**: THIS IS THE DEFINITIVE OPERATIONS GUIDE

---

## 🎯 PRIMARY REFERENCE

**MASTER DOCUMENT**: `FULL_PIPELINE_CONFIG_WITH_PWA.md` (Repository Root)

This SOP provides operational procedures for the locked AUREN configuration. All technical details are in the master document.

## 🔧 DAILY OPERATIONS

### Morning Health Check
```bash
# SSH to server
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218

# Run comprehensive health check
/root/monitor-auren.sh

# Expected output: All containers UP, all endpoints healthy
```

### Quick Status Verification
```bash
# Verify PWA is accessible
curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/

# Verify NEUROS via proxy
curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/neuros/health

# Should return: {"status":"healthy","service":"neuros-advanced"}
```

## 🚀 DEPLOYMENT PROCEDURES

### PWA Updates
```bash
# Navigate to PWA directory
cd auren-pwa

# Make changes to code
# Edit files as needed

# Deploy to production
git add .
git commit -m "Describe changes"
git push
vercel --prod --public  # CRITICAL: --public flag required

# Verify deployment
curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/
```

### Backend Updates
```bash
# SSH to server
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218

# Make changes to running containers
docker exec -it neuros-advanced /bin/bash
# Edit files as needed
# Exit container

# Restart affected services
docker restart neuros-advanced

# Verify health
docker logs neuros-advanced --tail 10
curl http://localhost:8000/health
```

## 🔍 MONITORING PROCEDURES

### Container Health
```bash
# Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check specific container logs
docker logs neuros-advanced --tail 20
docker logs biometric-production --tail 20
```

### Endpoint Monitoring
```bash
# Test all critical endpoints
curl http://localhost:8000/health     # NEUROS direct
curl http://localhost:8888/health     # Biometric direct

# Test proxy endpoints
curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/neuros/health
curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/biometric/health
```

### CORS Verification
```bash
# Test CORS headers
curl -H "Origin: https://auren-pwa.vercel.app" \
     -X OPTIONS \
     http://localhost:8000/health -v

# Should include: access-control-allow-origin header
```

## 🚨 TROUBLESHOOTING PROCEDURES

### Issue: PWA Shows Authentication Page
**Solution**: 
```bash
cd auren-pwa
vercel --prod --public --force
```

### Issue: NEUROS Not Responding
**Solution**:
```bash
ssh root@144.126.215.218
docker restart neuros-advanced
docker logs neuros-advanced --tail 30
```

### Issue: 502 Proxy Errors
**Diagnosis**:
```bash
# Check backend is running
ssh root@144.126.215.218
docker ps | grep neuros-advanced
curl http://localhost:8000/health

# If backend down, restart
docker restart neuros-advanced
```

### Issue: CORS Errors in Browser
**Solution**: CORS is configured. If errors persist:
```bash
# Verify CORS configuration hasn't changed
ssh root@144.126.215.218
docker exec -i neuros-advanced grep -A 10 "CORSMiddleware" /app/neuros_advanced_reasoning_simple.py
```

## 📊 PERFORMANCE MONITORING

### Key Metrics to Track
- Container uptime: Should be >99%
- Response times: <500ms for health endpoints
- Memory usage: <80% for all containers
- Disk usage: <90% (currently ~83%)

### Weekly Review
```bash
# Check system resources
ssh root@144.126.215.218
df -h                    # Disk usage
docker stats --no-stream # Container resources
```

## 🔐 SECURITY PROCEDURES

### Access Control
- SSH access via sshpass with documented password
- Vercel deployment requires proper git access
- No public database ports exposed

### Regular Security Checks
```bash
# Verify only expected ports are open
nmap 144.126.215.218

# Check for unusual connections
ssh root@144.126.215.218
netstat -tulpn | grep LISTEN
```

## 📝 CHANGE MANAGEMENT

### Before Making Changes
1. Read FULL_PIPELINE_CONFIG_WITH_PWA.md
2. Test in development environment first
3. Document the change purpose
4. Plan rollback procedure

### After Making Changes
1. Run full verification tests
2. Update documentation if needed
3. Monitor for 24 hours
4. Update change log

## 🎯 ESCALATION PROCEDURES

### Level 1: Standard Issues
- Use troubleshooting procedures above
- Check documentation
- Run monitor-auren.sh

### Level 2: Service Down
- Follow emergency restoration in FULL_PIPELINE_CONFIG_WITH_PWA.md
- Notify team if downtime >15 minutes

### Level 3: Configuration Corruption
- DO NOT make experimental changes
- Refer to locked configuration document
- Consider full service recreation using documented commands

---

**END OF SOP-001**

*This SOP provides operational procedures for the locked AUREN configuration. Technical details are in FULL_PIPELINE_CONFIG_WITH_PWA.md. Follow procedures exactly as documented.* 