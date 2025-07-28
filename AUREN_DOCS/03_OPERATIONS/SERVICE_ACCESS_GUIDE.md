# AUREN SERVICE ACCESS GUIDE
## All DevOps Tools & Dashboard Access

*Created: January 28, 2025*  
*Purpose: Central reference for accessing all AUREN services*

---

## 🌐 PUBLIC ENDPOINTS (External Access)

### Production Server
- **IP Address**: 144.126.215.218
- **Domain**: aupex.ai
- **SSH Access**: `sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218`

### Live Services

| Service | URL | Purpose | Status |
|---------|-----|---------|--------|
| **Main Website** | http://aupex.ai | AUREN landing page with 3D animations | ✅ LIVE |
| **Biometric API** | http://144.126.215.218:8888 | Webhook reception & processing | ✅ LIVE |
| **Health Check** | http://144.126.215.218:8888/health | System status JSON | ✅ LIVE |
| **Admin API** | http://144.126.215.218:8888/admin | Security management (requires API key) | ✅ LIVE |
| **Kafka UI** | http://144.126.215.218:8081 | Event stream monitoring | ❓ CHECK |

---

## 🐳 DOCKER SERVICES (Internal Access)

### Access Pattern
All internal services are accessed via SSH tunnel or from within containers:

```bash
# SSH into server first
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218

# Then access services locally
```

### Database Services

#### PostgreSQL (TimescaleDB)
- **Container**: auren-postgres
- **Internal Host**: auren-postgres:5432
- **External Access**: localhost:5432 (when SSH'd in)
- **Credentials**: 
  - User: `auren_user`
  - Password: `auren_secure_2025`
  - Database: `auren_production`
- **Connection String**: 
  ```
  postgresql://auren_user:auren_secure_2025@auren-postgres:5432/auren_production
  ```
- **Access Command**:
  ```bash
  docker exec -it auren-postgres psql -U auren_user -d auren_production
  ```

#### Redis
- **Container**: auren-redis
- **Internal Host**: auren-redis:6379
- **External Access**: localhost:6379 (when SSH'd in)
- **No Authentication Required**
- **Connection String**: `redis://auren-redis:6379/0`
- **Access Command**:
  ```bash
  docker exec -it auren-redis redis-cli
  ```

#### ChromaDB (Vector Database)
- **Container**: auren-chromadb
- **Internal Host**: auren-chromadb:8000
- **External Access**: localhost:8000 (when SSH'd in)
- **Purpose**: Vector embeddings for RAG
- **Access**: Via API only

### Monitoring Services

#### Prometheus ⚠️
- **Container**: auren-prometheus (if deployed)
- **Port**: 9090
- **Status**: NOT CONFIRMED DEPLOYED
- **Expected URL**: http://localhost:9090 (when SSH'd in)
- **Config Location**: `/prometheus.yml`
- **Check if running**:
  ```bash
  docker ps | grep prometheus
  ```

#### Grafana ⚠️
- **Container**: auren-grafana (if deployed)
- **Port**: 3000
- **Status**: NOT CONFIRMED DEPLOYED
- **Expected URL**: http://localhost:3000 (when SSH'd in)
- **Default Credentials**: admin/admin (first login)
- **Check if running**:
  ```bash
  docker ps | grep grafana
  ```

### Message Queue Services

#### Kafka
- **Container**: auren-kafka
- **Internal Host**: auren-kafka:9092
- **External Access**: localhost:9092 (when SSH'd in)
- **Topics**:
  - `biometric-events`
  - `agent-events`
  - `memory-access`
  - `hypothesis-updates`
  - `breakthrough-alerts`
- **List Topics**:
  ```bash
  docker exec auren-kafka kafka-topics --list --bootstrap-server localhost:9092
  ```
- **Monitor Events**:
  ```bash
  docker exec -it auren-kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic biometric-events \
    --from-beginning
  ```

#### Zookeeper
- **Container**: auren-zookeeper
- **Port**: 2181
- **Purpose**: Kafka coordination
- **Usually no direct access needed**

---

## 🔍 HOW TO CHECK SERVICE STATUS

### 1. View All Running Containers
```bash
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker ps'
```

### 2. Check Specific Service Health
```bash
# PostgreSQL
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker exec auren-postgres pg_isready'

# Redis
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker exec auren-redis redis-cli ping'

# Biometric API
curl http://144.126.215.218:8888/health | jq .
```

### 3. View Service Logs
```bash
# Recent logs
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker logs --tail 50 [container-name]'

# Follow logs
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker logs -f [container-name]'
```

---

## 🚨 MISSING SERVICES (Need Deployment)

Based on docker-compose.yml, these services are defined but NOT confirmed running:

1. **Prometheus** (Port 9090) - Metrics collection
2. **Grafana** (Port 3000) - Metrics visualization  
3. **Redis Exporter** (Port 9121) - Redis metrics for Prometheus
4. **Postgres Exporter** (Port 9187) - PostgreSQL metrics

### To Deploy Missing Services

```bash
# SSH into server
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218

# Check docker-compose.yml
cd /root/auren-deployment  # or wherever deployed
cat docker-compose.yml

# Start missing services
docker-compose up -d prometheus grafana redis-exporter postgres-exporter

# Verify they're running
docker ps
```

---

## 📊 DASHBOARD ACCESS SUMMARY

### Currently Available
- ✅ **Biometric API Health**: http://144.126.215.218:8888/health
- ✅ **Main Website**: http://aupex.ai
- ✅ **Admin API**: http://144.126.215.218:8888/admin (requires API key)

### Need Verification/Deployment
- ❓ **Kafka UI**: http://144.126.215.218:8081
- ❌ **Prometheus**: Would be at port 9090
- ❌ **Grafana**: Would be at port 3000

### Internal Only (via SSH)
- ✅ **PostgreSQL**: Via docker exec commands
- ✅ **Redis**: Via docker exec commands
- ✅ **ChromaDB**: API at port 8000

---

## 🔐 SECURITY NOTES

1. **Never expose internal ports** without proper security
2. **Use SSH tunnels** for secure access to internal services
3. **API keys required** for admin endpoints
4. **Monitor access logs** regularly

### SSH Tunnel Example (for local access)
```bash
# Forward Grafana to your local machine
ssh -L 3000:localhost:3000 root@144.126.215.218

# Then access at http://localhost:3000 on your machine
```

---

## 📝 TODO: Deploy Monitoring Stack

To get full monitoring capabilities:

1. Deploy Prometheus and Grafana
2. Configure dashboards for:
   - Biometric event processing
   - API performance metrics
   - Database health
   - Redis cache hit rates
3. Set up alerts for critical issues
4. Document access procedures

---

*Use this guide to access any AUREN service. Update when new services are deployed.* 