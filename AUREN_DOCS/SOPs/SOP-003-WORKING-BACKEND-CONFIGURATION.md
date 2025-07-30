# SOP-003: WORKING BACKEND CONFIGURATION - UPDATED WITH PWA

**Created**: January 30, 2025
**Updated**: January 30, 2025 (PWA Integration Complete)
**Status**: ✅ LOCKED CONFIGURATION - PRODUCTION READY
**Critical**: DO NOT MODIFY WITHOUT APPROVAL

## 🎯 REFERENCE DOCUMENT

**PRIMARY REFERENCE**: See `FULL_PIPELINE_CONFIG_WITH_PWA.md` in repository root for complete configuration details.

## ✅ VERIFIED WORKING STATE

### Backend Services - ALL OPERATIONAL
```bash
CONTAINER NAME          PORT    STATUS              PURPOSE
neuros-advanced         8000    ✅ RUNNING + CORS   AI Agent with CORS enabled
biometric-production    8888    ✅ RUNNING          Biometric data processing
auren-postgres          5432    ✅ RUNNING          TimescaleDB database
auren-redis             6379    ✅ RUNNING          Cache and sessions
auren-kafka             9092    ✅ RUNNING          Event streaming
auren-prometheus        9090    ✅ RUNNING          Metrics collection
auren-grafana           3000    ✅ RUNNING          Monitoring dashboards
```

### PWA Integration - FULLY FUNCTIONAL
- **Production URL**: https://auren-omacln1ad-jason-madrugas-projects.vercel.app
- **Proxy Configuration**: ✅ WORKING (Vercel → Backend HTTP)
- **CORS**: ✅ ENABLED (NEUROS accepts PWA requests)
- **Authentication**: ✅ DISABLED (--public flag used)

## 🔧 CRITICAL NEUROS CONFIGURATION

### Container Details (LOCKED)
```bash
Container: neuros-advanced
Image: neuros-advanced:final-v2
Network: auren-network
Port: 8000
Status: ✅ RUNNING with CORS
```

### CORS Configuration (DO NOT CHANGE)
```python
# File: /app/neuros_advanced_reasoning_simple.py
self.app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://auren-4yzu414cz-jason-madrugas-projects.vercel.app",
        "https://auren-pwa.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🚀 DEPLOYMENT PROCEDURES (LOCKED)

### Backend Maintenance
```bash
# SSH Access
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218

# Monitor System
/root/monitor-auren.sh

# Restart NEUROS (if needed)
docker restart neuros-advanced
```

### PWA Deployment
```bash
cd auren-pwa
git add .
git commit -m "Deploy changes"
git push
vercel --prod --public  # CRITICAL: --public disables auth
```

## ✅ VERIFICATION COMMANDS

### Test Complete Pipeline
```bash
# 1. PWA Loads
curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/
# Returns: HTML (not auth page)

# 2. NEUROS Health via Proxy
curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/neuros/health
# Returns: {"status":"healthy","service":"neuros-advanced"}

# 3. End-to-End Test
curl -X POST https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/neuros/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "Test", "user_id": "test", "session_id": "test"}'
# Returns: NEUROS conversation response
```

## 🚨 EMERGENCY RESTORATION

### If NEUROS Container Fails
```bash
ssh root@144.126.215.218
docker stop neuros-advanced
docker run -d --name neuros-advanced \
  --network auren-network \
  -p 8000:8000 \
  -e REDIS_URL=redis://auren-redis:6379 \
  -e POSTGRES_URL=postgresql://auren_user:auren_password@auren-postgres:5432/auren_production \
  -e KAFKA_BOOTSTRAP_SERVERS=auren-kafka:9092 \
  neuros-advanced:final-v2

# Then re-apply CORS using python script (see FULL_PIPELINE_CONFIG_WITH_PWA.md)
```

### If PWA Fails
```bash
cd auren-pwa
vercel --prod --public --force
```

## 📝 DOCUMENTATION HIERARCHY

1. **FULL_PIPELINE_CONFIG_WITH_PWA.md** (Master Reference)
2. **This SOP** (Quick Reference)
3. **CURRENT_SYSTEM_STATE.md** (Status Updates)
4. **monitor-auren.sh** (Health Checks)

## ⚠️ DEPRECATED CONFIGURATIONS

The following configurations are OBSOLETE and should NOT be used:
- Any docker-compose files with different container names
- Direct HTTP access from PWA (causes mixed content errors)
- Manual CORS configuration (use locked version only)
- Any authentication-enabled Vercel deployments

## 🎯 FOR FUTURE ENGINEERS

### Before Making Changes:
1. Read FULL_PIPELINE_CONFIG_WITH_PWA.md completely
2. Test changes in development environment first
3. Always verify end-to-end functionality after changes
4. Update documentation if configuration changes

### Critical Rules:
- NEVER change container names (neuros-advanced, biometric-production)
- NEVER change port mappings (8000, 8888)
- NEVER modify CORS origins without testing
- ALWAYS use `vercel --prod --public` for deployments
- ALWAYS test proxy endpoints after changes

---

**END OF SOP-003**

*This SOP reflects the final, tested, and locked configuration. Any deviations from this setup may break the PWA-backend communication.* 