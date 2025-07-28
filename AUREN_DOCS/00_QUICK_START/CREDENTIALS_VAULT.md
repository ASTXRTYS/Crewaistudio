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
- **Key**: `[REDACTED-OPENAI-API-KEY]`
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

## 🔐 SECTION 9: SECURITY ENHANCEMENT LAYER

### PHI Encryption
- **PHI_MASTER_KEY**: `OIixes55QW8WL7ky0Q7HDHYRTwKld8U0kQvrZnFrRhA=`
- **Algorithm**: AES-256-GCM with HKDF key derivation
- **Purpose**: HIPAA-compliant PHI encryption at rest
- **Created**: 2025-01-28

### Enhanced Webhook Secrets (Comma-separated for rotation)
- **OURA_WEBHOOK_SECRET**: `f62f68881a767d70e68c33ea6838ee30cc184236fe246eea2949d8e0b0e8a90f,48472b2ac542d7a09be5aaff871de00a82ca44afe29caa520281d0d57afe25f0`
- **WHOOP_WEBHOOK_SECRET**: `3cffe8ff206c9981ae10dab70fd99c40d7d107cbe25e5afdc2406b0b2512334c,2078799b92d7ac64a9b5fa85e1f4c4b484fea3dec3af470ebe9109f9bedfbeda`
- **APPLEHEALTH_WEBHOOK_SECRET**: `4251ed6108a8834e62447fb7565dd1da313135b2e6f5f8dd0cd03f9681583528,bf5b6cea694d0c9fabd5f1cfceb641e8de63835ab5db483fed183c386cde109f`
- **GARMIN_WEBHOOK_SECRET**: `b1d9c59063acb8c36d8050ab996c43613186a92917de0715c57f9e3ece4ad6c1,b62003b2a4ba2155b00ab4f37070dffde052f0b45e45af2e3a24795d36dc00a2`
- **FITBIT_WEBHOOK_SECRET**: `15e94fccfc0f657c533c4e9271bad165ccf30275797de585c2d2ac2aa64455cd,d46540be4c4f9f6f01be90bce89caa1895deda4715bcc579578682079ac0f9fa`

### Security Service Endpoints
- **Admin API**: http://144.126.215.218:8888/admin
- **Audit Logs**: http://144.126.215.218:8888/admin/audit-logs
- **API Key Management**: http://144.126.215.218:8888/admin/api-keys

### Initial Admin API Key
- **Key ID**: ak_96a217014a9c
- **API Key**: auren_WKfjsldLWvzubSJaV--FspQnTRT-fvnGRxr2_uQ_Y7w
- **Role**: admin
- **Purpose**: Initial system administration
- **Created**: 2025-01-28

*Note: Webhook signature verification is now ENABLED and REQUIRED*

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
| 2025-01-28 | Senior Engineer | Added Section 9 | Security enhancement credentials |

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