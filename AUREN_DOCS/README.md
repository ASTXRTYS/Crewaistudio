# AUREN DOCUMENTATION HUB - LOCKED CONFIGURATION

**Last Updated**: January 30, 2025 - LOCKED CONFIGURATION UPDATE  
**Status**: ✅ PRODUCTION READY - LOCKED CONFIGURATION

## 🚨 CRITICAL: LOCKED CONFIGURATION

**MASTER REFERENCE**: `AUREN_COMPLETE_SYSTEM_REFERENCE/` (Complete System Documentation)

⚠️ **FOR ANY ENGINEER**: If you're ever stuck or need to understand how AUREN is configured, refer to the `AUREN_COMPLETE_SYSTEM_REFERENCE/` folder. This is the SINGLE SOURCE OF TRUTH for our production system configuration.

This documentation hub reflects the **LOCKED** AUREN configuration. All setup is complete and operational.

---

## ✅ CURRENT SYSTEM STATUS (LOCKED)

### PRODUCTION READY - ALL SERVICES OPERATIONAL
```
Backend Services:   ✅ 7 containers running (neuros-advanced, biometric-production, etc.)
PWA Frontend:       ✅ Live at https://auren-pwa.vercel.app
Communication:      ✅ HTTPS→HTTP via Vercel proxy (CORS enabled)
Authentication:     ✅ Disabled (--public flag)
End-to-End:         ✅ Full NEUROS conversation working
Documentation:      ✅ Complete and current
```

**Configuration Locked**: January 30, 2025  
**Next Phase**: Feature development on stable foundation

---

## 🚀 QUICK START FOR NEW ENGINEERS

### 1. Read This First
- **[AUREN_COMPLETE_SYSTEM_REFERENCE/](../AUREN_COMPLETE_SYSTEM_REFERENCE/)** - 🎯 MASTER SYSTEM CONFIGURATION
- **[SOP-001: Master Operations Guide](SOPs/SOP-001-MASTER-OPERATIONS-GUIDE.md)** - Daily procedures  
- **[FULL_PIPELINE_CONFIG_WITH_PWA.md](../FULL_PIPELINE_CONFIG_WITH_PWA.md)** - Legacy reference

### 2. Verify System Status
```bash
# Test PWA access
curl https://auren-pwa.vercel.app/

# Test backend health via proxy
curl https://auren-pwa.vercel.app/api/neuros/health
```

### 3. Access Backend
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218
/root/monitor-auren.sh
```

---

## 🌐 LIVE SYSTEM ENDPOINTS (LOCKED)

### Production PWA
- **Primary**: https://auren-omacln1ad-jason-madrugas-projects.vercel.app
- **Status**: ✅ LIVE AND ACCESSIBLE
- **Features**: Full NEUROS conversation, no authentication required

### Backend APIs (via Proxy)
- **NEUROS**: `https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/neuros/health`
- **Biometric**: `https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/biometric/health`
- **Status**: ✅ PROXY ROUTING WORKING

### Direct Backend (Internal)
- **NEUROS**: http://144.126.215.218:8000
- **Biometric**: http://144.126.215.218:8888
- **Status**: ✅ CORS ENABLED, HTTP ENDPOINTS WORKING

---

## 📚 LOCKED DOCUMENTATION STRUCTURE

### 🔐 MASTER REFERENCES (START HERE)
- ✅ **[AUREN Backend Infrastructure Certification v1.0](01_ARCHITECTURE/AUREN_BACKEND_INFRASTRUCTURE_CERTIFICATION.md)** - 🏆 **CERTIFIED PRODUCTION STANDARD**
- ✅ **[FULL_PIPELINE_CONFIG_WITH_PWA.md](../FULL_PIPELINE_CONFIG_WITH_PWA.md)** - Complete technical configuration
- ✅ **[SOP-001: Master Operations Guide](SOPs/SOP-001-MASTER-OPERATIONS-GUIDE.md)** - Daily operational procedures
- ✅ **[CONFIGURATION_LOCK_SUMMARY.md](../CONFIGURATION_LOCK_SUMMARY.md)** - Lock completion summary

### 📋 OPERATIONAL GUIDES
- ✅ **[SOP-003: Working Backend Configuration](SOPs/SOP-003-WORKING-BACKEND-CONFIGURATION.md)** - Backend technical details
- ✅ **[Current System State](CURRENT_SYSTEM_STATE.md)** - Live system status and metrics
- ✅ **[Monitor Script](../monitor-auren.sh)** - Automated health check script (server)

### 🔐 ACCESS & SECURITY
- ✅ **[Credentials Vault](00_QUICK_START/CREDENTIALS_VAULT.md)** - All passwords and access credentials *(UPDATED: PostgreSQL password corrected)*
- ✅ **[SSH Access Standard](00_QUICK_START/SSH_ACCESS_STANDARD.md)** - Connection procedures

### 🌐 PWA CONFIGURATION (LOCKED)
- ✅ **[auren-pwa/vercel.json](../auren-pwa/vercel.json)** - Proxy routing configuration
- ✅ **[auren-pwa/src/utils/api.js](../auren-pwa/src/utils/api.js)** - API endpoint configuration
- ✅ **[auren-pwa/src/utils/websocket.js](../auren-pwa/src/utils/websocket.js)** - WebSocket handling

### 📖 DOCUMENTATION ORGANIZATION
- ✅ **[Documentation Organization Guide](01_ARCHITECTURE/DOCUMENTATION_ORGANIZATION_GUIDE.md)** - Complete navigation map

### 🚨 RECENT CRITICAL UPDATES (July 30, 2025)
- ✅ **[Enterprise Bridge Complete Setup](02_DEPLOYMENT/AUREN_ENTERPRISE_BRIDGE_COMPLETE_SETUP_REPORT.md)** - 1,796-line bridge + Terra Kafka strategy
- ✅ **[Biometric System Troubleshooting](02_DEPLOYMENT/BIOMETRIC_SYSTEM_DEPLOYMENT_GUIDE.md#troubleshooting)** - Authentication & startup fixes
- ✅ **[Updated Credentials](00_QUICK_START/CREDENTIALS_VAULT.md)** - PostgreSQL password corrected (`auren_password_2024`)
- 🚀 **[Production Enhancements Guide](02_DEPLOYMENT/BIOMETRIC_BRIDGE_PRODUCTION_ENHANCEMENTS_GUIDE.md)** - CircuitBreaker + Enhanced Kafka Producer (OPERATIONAL)
- 🎯 **[HANDOFF REPORT](HANDOFF_REPORT_ENTERPRISE_BRIDGE_SESSION.md)** - Complete session summary for next engineer

---

## 🔧 LOCKED SYSTEM ARCHITECTURE

### Backend (LOCKED - DO NOT CHANGE)
```
Server: 144.126.215.218 (DigitalOcean)
Container Names: neuros-advanced, biometric-production
Ports: 8000 (NEUROS), 8888 (Biometric)
Network: auren-network
CORS: Enabled for Vercel domains
Status: ✅ OPERATIONAL
```

### PWA (LOCKED - DO NOT CHANGE)
```
Framework: Vite + React
Deployment: Vercel (--public flag required)
Proxy Paths: /api/neuros, /api/biometric
Authentication: DISABLED
Status: ✅ FULLY FUNCTIONAL
```

### Communication Flow (LOCKED)
```
User Browser (HTTPS)
    ↓
Vercel PWA
    ↓
Vercel Proxy (/api/neuros → http://144.126.215.218:8000)
    ↓
NEUROS Backend (HTTP + CORS)
    ↓
Response with AI conversation
```

---

## 🚀 DEPLOYMENT PROCEDURES (LOCKED)

### PWA Updates
```bash
cd auren-pwa
git add . && git commit -m "Changes" && git push
vercel --prod --public  # CRITICAL: --public flag required
```

### Backend Updates
```bash
ssh root@144.126.215.218
# Make changes to containers
docker restart neuros-advanced  # if needed
/root/monitor-auren.sh  # verify health
```

---

## ✅ VERIFICATION COMMANDS (LOCKED SYSTEM)

### Complete System Test
```bash
# 1. PWA loads without authentication
curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/

# 2. NEUROS health via proxy
curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/neuros/health

# 3. End-to-end conversation test
curl -X POST https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/neuros/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "Test", "user_id": "test", "session_id": "test"}'
```

**Expected Results**: All commands return success responses

---

## 🚫 DEPRECATED DOCUMENTATION

**DO NOT USE** (marked obsolete):
- ❌ Old docker-compose references with different names
- ❌ Direct HTTP PWA access patterns
- ❌ Manual CORS configurations
- ❌ Authentication-enabled deployment guides
- ❌ Any non-standard container naming

---

## 🎯 FOR FUTURE ENGINEERS

### Getting Started
1. **Read**: `FULL_PIPELINE_CONFIG_WITH_PWA.md` (complete technical reference)
2. **Understand**: System is fully operational and locked
3. **Follow**: SOP-001 for daily operations
4. **Build**: New features on stable foundation

### Development Guidelines
- Backend changes: SSH to server, modify code, restart containers
- Frontend changes: Edit PWA, commit, push, `vercel --prod --public`
- Always test proxy endpoints after changes
- Document architectural changes in master reference

### Critical Rules
- NEVER change container names (neuros-advanced, biometric-production)
- NEVER change port mappings (8000, 8888)
- NEVER modify CORS origins without testing
- ALWAYS use `vercel --prod --public` for deployments
- ALWAYS reference locked configuration for guidance

---

## 🚨 EMERGENCY PROCEDURES

### System Down
1. SSH: `sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218`
2. Check: `/root/monitor-auren.sh`
3. Restore: Follow procedures in `FULL_PIPELINE_CONFIG_WITH_PWA.md`

### PWA Issues
1. Redeploy: `cd auren-pwa && vercel --prod --public --force`
2. Verify: Test endpoints above

---

## 📝 DOCUMENTATION MAINTENANCE

### When to Update
- Major architectural changes (rare, requires approval)
- New documentation structure (follow locked patterns)
- Updated deployment procedures (test thoroughly)

### What NOT to Change
- Locked configuration references
- Container naming standards
- Port mapping documentation
- CORS configuration details
- Proxy routing patterns

---

**END OF DOCUMENTATION HUB**

*This documentation reflects the locked AUREN configuration. The system is production-ready and fully operational. All procedures have been tested and verified. Future development should build upon this stable foundation.* 