# PROMETHEUS FIX TROUBLESHOOTING PLAYBOOK

**Created**: January 28, 2025  
**Author**: Senior Engineer  
**Version**: 1.0  
**Purpose**: Step-by-step playbook documenting the exact fix process

---

## 🔧 The Complete Fix Journey

### Step 1: Initial Discovery (Container Name Mismatch)

**Expected**: biometric-system-100  
**Actual**: biometric-production

```bash
# What I ran:
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker ps | grep biometric'

# Result:
d16f6dfba834   auren/biometric-complete:latest   biometric-production
```

**Learning**: Always verify container names; documentation may be outdated.

---

### Step 2: File Discovery (Wrong API File)

**Expected**: /app/api.py  
**Actual**: /app/complete_biometric_system.py

```bash
# Discovery commands:
docker inspect biometric-production | grep -A 10 "Cmd"
# Found: "python complete_biometric_system.py"

docker exec biometric-production find /app -name "api.py" -type f
# Found: /app/api.py exists but isn't used!
```

**Learning**: The Dockerfile CMD determines which file runs, not file names.

---

### Step 3: Missing Metrics Endpoint

**Problem**: complete_biometric_system.py had no /metrics endpoint

```bash
# Verification:
docker exec biometric-production grep -n "@app.get.*metrics" /app/complete_biometric_system.py
# Result: Nothing found
```

**Initial Failed Attempts**:
1. Tried complex regex replacements → Broke Python syntax
2. Created api_metrics_fix.py with full implementation → Too complex
3. Multiple sed attempts → Corrupted try/except blocks

**Successful Fix**:
```python
# Simple addition to complete_biometric_system.py:
@app.get("/metrics")
async def get_metrics():
    """Expose Prometheus metrics"""
    if PROMETHEUS_AVAILABLE:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    else:
        return {"error": "Prometheus metrics not available"}
```

---

### Step 4: Dependency Hell Journey

**Cascade of Issues**:
```
1. prometheus-fastapi-instrumentator==7.1.0 installed
   ↓
2. Upgraded starlette to 0.47.2 (breaking FastAPI)
   ↓
3. Container restart loop (SyntaxError)
   ↓
4. Downgraded starlette to 0.27.0
   ↓
5. Downgraded instrumentator to 5.11.2
   ↓
6. SUCCESS
```

**Commands Used**:
```bash
# Install dependencies
docker exec biometric-production pip install prometheus-fastapi-instrumentator psutil

# Fix version conflict
docker exec biometric-production pip install starlette==0.27.0
docker exec biometric-production pip install prometheus-fastapi-instrumentator==5.11.2
```

---

### Step 5: Missing Import Fix

**Error**: NameError: name 'Response' is not defined

```bash
# Quick fix:
docker exec biometric-production sed -i "s/from fastapi import FastAPI/from fastapi import FastAPI, Response/" /app/complete_biometric_system.py
```

---

### Step 6: Network Configuration Fix

**Problem**: Prometheus couldn't scrape the API  
**Cause**: Using external IP instead of container name

```yaml
# Bad (prometheus.yml):
- targets: ['144.126.215.218:8888']

# Good:
- targets: ['biometric-production:8888']
```

**Verification**:
```bash
# Ensure both on same network
docker network connect auren-network biometric-production
docker network connect auren-network auren-prometheus
```

---

## 📋 Complete Command Sequence

```bash
# 1. Identify container
docker ps | grep biometric

# 2. Create metrics fix
cat > simple_metrics_fix.py << 'EOF'
[metrics implementation]
EOF

# 3. Deploy fix
scp simple_metrics_fix.py root@144.126.215.218:/opt/auren_deploy/
ssh root@144.126.215.218 'cd /opt/auren_deploy && python3 simple_metrics_fix.py'

# 4. Copy fixed file to container
docker cp /opt/auren_deploy/complete_biometric_system_fixed.py biometric-production:/app/complete_biometric_system.py

# 5. Fix imports
docker exec biometric-production sed -i "s/from fastapi import FastAPI/from fastapi import FastAPI, Response/" /app/complete_biometric_system.py

# 6. Restart container
docker restart biometric-production

# 7. Verify metrics work
curl http://localhost:8888/metrics

# 8. Fix Prometheus config
vim /opt/auren_deploy/prometheus.yml
docker restart auren-prometheus

# 9. Verify scraping
curl http://localhost:9090/api/v1/targets | jq
```

---

## 🎯 Key Files Created

1. **api_metrics_fix.py** - Full metrics implementation (future use)
2. **simple_metrics_fix.py** - Script that actually fixed the issue
3. **prometheus-fixed.yml** - Working Prometheus configuration
4. **fix_complete_biometric_metrics.py** - Failed attempt (syntax issues)
5. **fix_metrics_properly.py** - Another failed attempt

---

## ⚠️ Lessons Learned

1. **Start Simple**: Complex regex replacements break Python syntax
2. **Check Dependencies**: Version conflicts cascade quickly
3. **Verify Container Names**: Documentation may be wrong
4. **Test Incrementally**: Fix one thing at a time
5. **Backup First**: Always copy files before modifying

---

*This playbook documents the exact journey from broken metrics to working observability.* 