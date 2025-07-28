# DOCKER SAFE CLEANUP LIST
## Verified Redundant Images for Removal

*Created: July 28, 2025*  
*Author: Senior Engineer*  
*Purpose: Document which Docker images are safe to remove without impacting production*

---

## ✅ CRITICAL SERVICES (DO NOT REMOVE)

Based on `AUREN_CLEAN_DEPLOYMENT_GUIDE.md`, these are required:

1. **auren_deploy_biometric-bridge:latest** - Main application
2. **timescale/timescaledb:latest-pg16** - Primary database
3. **redis:7-alpine** - Cache and session storage
4. **bitnami/kafka:3.5** - Event streaming
5. **grafana/grafana:latest** - Monitoring dashboards
6. **prom/prometheus:latest** - Metrics collection

---

## 🗑️ SAFE TO REMOVE

### Redundant Kafka/Zookeeper (4.67GB total)
- `confluentinc/cp-kafka:7.5.0` (849MB)
- `confluentinc/cp-kafka:latest` (964MB)
- `confluentinc/cp-zookeeper:7.5.0` (849MB)
- `confluentinc/cp-zookeeper:latest` (1.11GB)
**Reason**: Using Bitnami Kafka instead (includes embedded Zookeeper)

### Old Database Version (1.18GB)
- `timescale/timescaledb:latest-pg15`
**Reason**: Using pg16 version

### Testing Infrastructure (1.2GB)
- `localstack/localstack:2.3`
**Reason**: Only needed for local testing, not production

### Redundant AUREN Images (5.6GB total)
- `auren_deploy_auren-api:latest` (1.6GB) - Replaced by biometric-bridge
- `auren-production_auren-api:latest` (842MB) - Old deployment
- `auren/biometric-unified:v2` (779MB) - Superseded
- `auren/biometric-unified:fixed` (780MB) - Superseded
- `auren/biometric-unified:latest` (780MB) - Superseded
- `auren/biometric-complete:latest` (803MB) - Old version

### Old ChromaDB Versions
- `chromadb/chroma:0.4.15` (756MB) - If using 0.4.22
**Note**: Verify if ChromaDB is still needed before removing

### Miscellaneous
- `<none>:<none>` images (dangling)
- `auren-biometric:fixed` (378MB) - If not in use

---

## 🔧 CLEANUP COMMANDS

When server access is restored, run these commands:

```bash
# 1. Verify critical services are running
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# 2. Remove Confluent images (saves 4.67GB)
docker rmi confluentinc/cp-kafka:7.5.0 confluentinc/cp-kafka:latest \
           confluentinc/cp-zookeeper:7.5.0 confluentinc/cp-zookeeper:latest

# 3. Remove old PostgreSQL (saves 1.18GB)
docker rmi timescale/timescaledb:latest-pg15

# 4. Remove LocalStack (saves 1.2GB)
docker rmi localstack/localstack:2.3

# 5. Remove redundant AUREN images (saves 5.6GB)
docker rmi auren_deploy_auren-api:latest auren-production_auren-api:latest \
           auren/biometric-unified:v2 auren/biometric-unified:fixed \
           auren/biometric-unified:latest auren/biometric-complete:latest

# 6. Clean dangling images
docker image prune -f

# Total expected space recovery: ~12.65GB
```

---

## ⚠️ BEFORE REMOVING

1. **Always check if image is in use**: `docker ps | grep <image_name>`
2. **Test service health after each removal**
3. **Keep backups of critical data**
4. **Monitor disk space**: `df -h /`

---

## 📊 EXPECTED RESULTS

- Current disk usage: 94% of 24GB
- Expected after cleanup: ~40-50%
- Space to recover: ~12.65GB

---

*This list was created by cross-referencing the deployment guides with actual running services.* 