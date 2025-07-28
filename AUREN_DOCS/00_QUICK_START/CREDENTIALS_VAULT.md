# AUREN CREDENTIALS VAULT
## 🔐 CONFIDENTIAL - AUTHORIZED ACCESS ONLY

*Last Updated: July 28, 2025*  
*Next Rotation: August 28, 2025*

---

⚠️ **SECURITY NOTICE**: This document contains sensitive credentials. Handle with extreme care.

---

## 🖥️ SERVER ACCESS

### Primary Production Server
- **IP Address**: 144.126.215.218
- **Provider**: DigitalOcean
- **OS**: Ubuntu 25.04

#### SSH Access
- **Username**: root
- **Password**: `.HvddX+@6dArsKd`
- **Port**: 22 (default)
- **Method**: sshpass (REQUIRED)

#### SSH Command Template:
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218
```

---

## 🗄️ DATABASE CREDENTIALS

### PostgreSQL/TimescaleDB
- **Host (Internal)**: auren-postgres
- **Host (External)**: localhost:5432
- **Database**: auren_production
- **Username**: auren_user
- **Current Password**: `auren_secure_2025`
- **Previous Password**: `securepwd123!` (DEPRECATED - DO NOT USE)
- **Port**: 5432

#### Connection String:
```
postgresql://auren_user:auren_secure_2025@auren-postgres:5432/auren_production
```

### Redis
- **Host**: auren-redis
- **Port**: 6379
- **Password**: None (no auth configured)
- **Database**: 0

#### Connection String:
```
redis://auren-redis:6379/0
```

---

## 🔑 API KEYS

### OpenAI
- **Key**: `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`
- **Purpose**: NEUROS cognitive processing
- **Billing**: Check usage at platform.openai.com

### Device API Keys (Placeholders)
- **Oura Client ID**: `placeholder`
- **Oura Client Secret**: `placeholder`
- **WHOOP API Key**: `placeholder`
- **Garmin Key**: `placeholder`
- **Fitbit Key**: `placeholder`

---

## 🌐 SERVICE ENDPOINTS

### Public Endpoints
- **Main Website**: http://aupex.ai (144.126.215.218:80)
- **Biometric API**: http://144.126.215.218:8888
- **Kafka UI**: http://144.126.215.218:8081

### Internal Docker Network
- **Network Name**: auren-network
- **Kafka**: auren-kafka:9092
- **Zookeeper**: auren-zookeeper:2181

---

## 🐳 DOCKER SERVICES

### Container Names & Purposes
1. **biometric-system-100** - Main biometric processing service
2. **auren-postgres** - TimescaleDB database
3. **auren-redis** - Memory cache
4. **auren-kafka** - Event streaming
5. **auren-zookeeper** - Kafka coordination
6. **auren-chromadb** - Vector database
7. **auren-kafka-ui** - Kafka management interface

---

## 🔒 WEBHOOK SECRETS

### Device Webhook Verification
- **Oura**: `oura_secret_2025`
- **WHOOP**: `whoop_secret_2025`
- **Apple Health**: `apple_secret_2025`
- **Garmin**: `garmin_secret_2025`
- **Fitbit**: `fitbit_secret_2025`

*Note: Signature verification currently disabled in production*

---

## 📁 CRITICAL FILE PATHS

### On Server
- **Application Code**: `/opt/auren_deploy/`
- **Environment File**: `/opt/auren_deploy/.env`
- **NEUROS Config**: `/opt/auren_deploy/config/neuros_agent_profile.yaml`
- **Logs**: `/opt/auren/logs/`
- **Biometric Schema**: `/tmp/biometric_schema.sql`

### Docker Volumes
- **PostgreSQL Data**: `/var/lib/postgresql/data`
- **Redis Data**: `/data`
- **Kafka Data**: `/var/lib/kafka/data`

---

## 🚨 EMERGENCY ACCESS

### Root PostgreSQL Access
```bash
docker exec -it auren-postgres psql -U postgres
```

### Redis CLI Access
```bash
docker exec -it auren-redis redis-cli
```

### Kafka Console
```bash
docker exec -it auren-kafka /bin/kafka-console-consumer --bootstrap-server localhost:9092 --topic biometric-events --from-beginning
```

---

## 🔄 ROTATION SCHEDULE

### Monthly Rotation Required:
- [ ] SSH root password
- [ ] PostgreSQL passwords
- [ ] Webhook secrets

### Quarterly Rotation:
- [ ] API keys (where possible)
- [ ] Docker registry credentials

### Annual:
- [ ] Server SSH keys
- [ ] SSL certificates

---

## 📝 ACCESS LOG

| Date | User | Action | Details |
|------|------|--------|---------|
| 2025-07-28 | Senior Engineer | Created vault | Initial documentation |
| 2025-07-28 | Senior Engineer | Updated PostgreSQL | Changed password to auren_secure_2025 |

---

## ⚡ QUICK COMMANDS

### Full System Health Check
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'curl -s http://localhost:8888/health | jq .'
```

### View Recent Biometric Events
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'docker exec -e PGPASSWORD=auren_secure_2025 auren-postgres psql -U auren_user -d auren_production -c "SELECT * FROM biometric_events ORDER BY created_at DESC LIMIT 5;"'
```

### Restart All Services
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'docker restart biometric-system-100 auren-kafka auren-postgres auren-redis'
```

---

## 🛡️ SECURITY PROTOCOLS

1. **Never share this document via email or chat**
2. **Store encrypted copy only**
3. **Access on need-to-know basis**
4. **Log all credential usage**
5. **Rotate immediately if compromised**
6. **Use sshpass for all automated access**

---

*END OF CREDENTIALS VAULT* 