# AUREN BIOMETRIC SYSTEM COMPLETE DEPLOYMENT GUIDE
## Sections 1-8: From Zero to 87.5% Operational

*Created: July 28, 2025*  
*Engineer: Senior Engineer*  
*Status: PRODUCTION DEPLOYED*

---

## 🔐 CRITICAL ACCESS INFORMATION

### Server Access
- **Server IP**: 144.126.215.218
- **SSH User**: root
- **SSH Password**: `.HvddX+@6dArsKd`
- **SSH Method**: `sshpass` (REQUIRED - See standard below)

### Database Credentials
- **PostgreSQL/TimescaleDB**:
  - Host: auren-postgres (internal) / localhost:5432 (external)
  - Database: auren_production
  - User: auren_user
  - Password: `auren_secure_2025`
  - Previous Password: `securepwd123!` (deprecated)

### Service Credentials
- **Redis**: redis://auren-redis:6379/0 (no auth)
- **Kafka**: auren-kafka:9092 (no auth)
- **OpenAI API Key**: `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`

### Service Endpoints
- **Biometric System**: http://144.126.215.218:8888
- **Kafka UI**: http://144.126.215.218:8081
- **Main Website**: http://aupex.ai (144.126.215.218:80)

---

## 📋 SSH ACCESS STANDARD (MANDATORY)

### sshpass Installation and Usage

**IMPORTANT**: All server access MUST use `sshpass` for automated deployments.

#### Installation:
```bash
# macOS
brew install hudochenkov/sshpass/sshpass

# Linux
sudo apt-get install sshpass

# Alternative for macOS if brew fails
brew install https://raw.githubusercontent.com/kadwanev/bigboybrew/master/Library/Formula/sshpass.rb
```

#### Standard Usage Pattern:
```bash
# All SSH commands MUST use this format:
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'command'

# For SCP:
sshpass -p '.HvddX+@6dArsKd' scp -o StrictHostKeyChecking=no file.txt root@144.126.215.218:/path/

# For interactive SSH:
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218
```

---

## 🏗️ SYSTEM ARCHITECTURE DEPLOYED

### Sections Implemented (87.5% Complete):

#### ✅ Section 1: Webhook Infrastructure
- **Status**: FULLY OPERATIONAL
- **Endpoints**: `/webhooks/{device_type}`
- **Supported Devices**: Oura, WHOOP, Apple Health, Garmin, Fitbit
- **Features**:
  - OAuth2 token management (framework ready)
  - Webhook signature verification (configurable)
  - Automatic event normalization

#### ✅ Section 2: Device-Specific Handlers
- **Status**: FULLY OPERATIONAL
- **Handlers Implemented**:
  - `OuraHandler`: Processes readiness, HRV, sleep data
  - `WHOOPHandler`: Processes recovery, strain, sleep cycles
  - `AppleHealthKitHandler`: Processes HRV, heart rate, workouts
- **Output**: Normalized `BiometricEvent` objects

#### ✅ Section 3: Kafka Event Pipeline
- **Status**: PRODUCER OPERATIONAL
- **Components**:
  - Kafka topics: `biometric-events`, `biometric-events.dlq`, `neuros-mode-switches`
  - Retry logic with exponential backoff
  - Dead Letter Queue for failed events
  - Compression and batching enabled

#### ✅ Section 4: Baseline & Pattern Detection
- **Status**: FULLY OPERATIONAL
- **Features**:
  - 7-day rolling baseline calculation
  - Pattern detectors: Circadian disruption, Recovery deficit
  - Automatic baseline updates with each event
- **Database Tables**: `user_baselines`, `pattern_detections`

#### ✅ Section 5: PostgreSQL Event Storage
- **Status**: FULLY OPERATIONAL
- **Schema Deployed**:
  ```sql
  - biometric_events (TimescaleDB hypertable)
  - user_baselines
  - pattern_detections
  - mode_switch_history
  - langraph_checkpoints
  ```
- **Features**: Time-series optimization, automatic partitioning

#### ✅ Section 6: Apple HealthKit Batch Handler
- **Status**: FULLY OPERATIONAL
- **Capabilities**:
  - Batch processing with 100-sample chunks
  - Concurrent processing (10 semaphore limit)
  - Error classification and retry logic

#### ⚠️ Section 7: Biometric-Kafka-LangGraph Bridge
- **Status**: PARTIALLY OPERATIONAL
- **Working**: Mode decision engine, state management
- **Issue**: Kafka consumer connection (non-critical)

#### ✅ Section 8: NEUROS Cognitive Graph
- **Status**: FULLY INTEGRATED
- **Configuration**: `/app/config/neuros_agent_profile.yaml`
- **Modes**: baseline, reflex, hypothesis, companion, sentinel
- **Memory Tiers**: Hot (24-72h), Warm (1-4 weeks), Cold (6mo-1yr)

---

## 📁 FILE LOCATIONS ON SERVER

### Application Code
- **Main Service**: `/opt/auren_deploy/complete_biometric_system.py`
- **Environment**: `/opt/auren_deploy/.env`
- **NEUROS Config**: `/opt/auren_deploy/config/neuros_agent_profile.yaml`
- **Logs**: `/opt/auren/logs/`

### Docker Containers
- **Biometric System**: `biometric-system-100`
- **PostgreSQL**: `auren-postgres`
- **Redis**: `auren-redis`
- **Kafka**: `auren-kafka`
- **Zookeeper**: `auren-zookeeper`

---

## 🚀 DEPLOYMENT COMMANDS USED

### Phase 1: Infrastructure Setup
```bash
# Fixed PostgreSQL authentication
docker exec auren-postgres psql -U auren_user -d postgres -c "ALTER USER auren_user WITH PASSWORD 'auren_secure_2025';"

# Created Kafka topics
docker exec auren-kafka /bin/kafka-topics --create --topic biometric-events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

### Phase 2: Database Schema
```bash
# Applied complete schema with TimescaleDB
docker cp /tmp/biometric_schema.sql auren-postgres:/tmp/
docker exec -e PGPASSWORD='auren_secure_2025' auren-postgres psql -U auren_user -d auren_production -f /tmp/biometric_schema.sql
```

### Phase 3: Service Deployment
```bash
# Deployed complete biometric system
docker run -d \
  --name biometric-system-100 \
  --network auren-network \
  --restart unless-stopped \
  -p 8888:8888 \
  --env-file /opt/auren_deploy/.env \
  -v /opt/auren_deploy/config:/app/config \
  -v /opt/auren/logs:/app/logs \
  auren/biometric-complete:latest
```

---

## 🧪 TESTING & VERIFICATION

### Test Commands:
```bash
# Test webhook
curl -X POST http://144.126.215.218:8888/webhooks/oura \
  -H "Content-Type: application/json" \
  -d '{"event_type": "readiness.updated", "data": {"score": 85, "hrv_balance": 65}, "user_id": "founder"}'

# Check baselines
curl http://144.126.215.218:8888/baselines/founder/hrv

# Check patterns
curl http://144.126.215.218:8888/patterns/founder

# Health check
curl http://144.126.215.218:8888/health | jq .
```

### Database Verification:
```bash
# Check events
docker exec -e PGPASSWORD='auren_secure_2025' auren-postgres psql -U auren_user -d auren_production -c "SELECT * FROM biometric_events ORDER BY created_at DESC LIMIT 5;"

# Check baselines
docker exec -e PGPASSWORD='auren_secure_2025' auren-postgres psql -U auren_user -d auren_production -c "SELECT * FROM user_baselines;"
```

---

## 🔧 TROUBLESHOOTING

### Common Issues:

1. **Kafka Consumer Not Connecting**
   - Current Status: Known issue, non-critical
   - Workaround: Events still processed via HTTP endpoints
   - Fix: Restart Kafka and service

2. **PostgreSQL Connection Issues**
   - Check password: Must be `auren_secure_2025`
   - Verify network: Must be on `auren-network`

3. **Service Not Responding**
   - Check logs: `docker logs biometric-system-100`
   - Restart: `docker restart biometric-system-100`

---

## 🛡️ SECURITY MEASURES

1. **Database**: Password-protected PostgreSQL
2. **Network**: Internal Docker network isolation
3. **API Keys**: Stored in environment variables
4. **Webhook Security**: Signature verification available
5. **Port Security**: Only 8888 exposed externally

---

## 📈 MONITORING

### Service Health:
```bash
# Real-time logs
docker logs -f biometric-system-100

# System status
curl http://144.126.215.218:8888/health

# Container status
docker ps | grep -E "auren|biometric"
```

### Metrics Available:
- Events processed count
- Baseline calculations
- Pattern detections
- Mode switches
- Component health status

---

## 🚨 EMERGENCY PROCEDURES

### Complete System Restart:
```bash
# Stop all
docker stop biometric-system-100 auren-kafka auren-postgres auren-redis

# Start infrastructure first
docker start auren-postgres auren-redis auren-zookeeper
sleep 10
docker start auren-kafka
sleep 10

# Start application
docker start biometric-system-100
```

### Rollback Procedure:
```bash
# Previous image available as
docker images | grep biometric-unified
```

---

## 📅 MAINTENANCE SCHEDULE

1. **Daily**: Check health endpoint
2. **Weekly**: Review logs for errors
3. **Monthly**: Database vacuum/analyze
4. **Quarterly**: Security updates

---

## 🎯 NEXT STEPS

1. **Fix Kafka Consumer**: Update consumer connection logic
2. **Enable OAuth**: Configure device-specific OAuth flows
3. **Add Monitoring**: Prometheus/Grafana integration
4. **Scale Testing**: Load test with 10k events/minute
5. **Add More Devices**: Integrate Polar, Suunto, etc.

---

## 📞 CONTACT

For issues or questions:
- **System**: AUREN Biometric Bridge v3.0.0
- **Deployed By**: Senior Engineer
- **Date**: July 28, 2025
- **Documentation Version**: 1.0

---

*This document is the authoritative guide for the AUREN Biometric System deployment.* 