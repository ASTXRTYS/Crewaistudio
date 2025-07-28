# AUREN CLEAN DEPLOYMENT GUIDE
## The Definitive Guide to Deploying AUREN Correctly

*Created: July 28, 2025*  
*Author: Senior Engineer*  
*Purpose: Single source of truth for AUREN deployment*  
*Status: VERIFIED WORKING ✅*

---

## 🎯 OVERVIEW

This guide provides the **ONLY** approved method for deploying AUREN. Following this guide ensures:
- Consistent deployments
- No conflicting configurations
- Proper service connectivity
- OpenAI integration working
- All endpoints functional

---

## 📋 PRE-DEPLOYMENT CHECKLIST

Before deployment, verify:

- [ ] Server access: `ssh root@144.126.215.218`
- [ ] Disk space > 30% free: `df -h /`
- [ ] Docker installed: `docker --version`
- [ ] Network created: `docker network ls | grep auren-network`
- [ ] No conflicting services: `docker ps | grep 8888`

---

## 🏗️ INFRASTRUCTURE SETUP

### 1. Create Docker Network
```bash
docker network create auren-network 2>/dev/null || echo "Network exists"
```

### 2. Start Database Services
```bash
# PostgreSQL with TimescaleDB
docker run -d \
  --name auren-postgres \
  --network auren-network \
  -p 5432:5432 \
  -e POSTGRES_USER=auren_user \
  -e POSTGRES_PASSWORD=auren_password_2024 \
  -e POSTGRES_DB=auren_production \
  -v postgres_data:/var/lib/postgresql/data \
  --restart unless-stopped \
  timescale/timescaledb:latest-pg16

# Redis
docker run -d \
  --name auren-redis \
  --network auren-network \
  -p 6379:6379 \
  -v redis_data:/data \
  --restart unless-stopped \
  redis:7-alpine

# Kafka (with embedded Zookeeper)
docker run -d \
  --name auren-kafka \
  --network auren-network \
  -p 9092:9092 \
  -e KAFKA_CFG_NODE_ID=0 \
  -e KAFKA_CFG_PROCESS_ROLES=controller,broker \
  -e KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 \
  -e KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT \
  -e KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=0@kafka:9093 \
  -e KAFKA_CFG_CONTROLLER_LISTENER_NAMES=CONTROLLER \
  --restart unless-stopped \
  bitnami/kafka:3.5
```

### 3. Verify Infrastructure
```bash
# Check all services are running
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "postgres|redis|kafka"

# Test connections
docker exec auren-postgres pg_isready -U auren_user
docker exec auren-redis redis-cli ping
docker exec auren-kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

---

## 🚀 BIOMETRIC SERVICE DEPLOYMENT

### The ONLY Approved Configuration:

```bash
docker run -d \
  --name biometric-production \
  --network auren-network \
  -p 8888:8888 \
  -e POSTGRES_HOST=auren-postgres \
  -e POSTGRES_USER=auren_user \
  -e POSTGRES_PASSWORD=auren_password_2024 \
  -e POSTGRES_DB=auren_production \
  -e REDIS_HOST=auren-redis \
  -e KAFKA_BOOTSTRAP_SERVERS=auren-kafka:9092 \
  -e OPENAI_API_KEY="sk-proj-YOUR_ACTUAL_KEY_HERE" \
  -e ENVIRONMENT=production \
  -e DISABLE_TEST_EVENTS=false \
  --restart unless-stopped \
  auren_deploy_biometric-bridge:latest
```

### ⚠️ CRITICAL NOTES:
1. **Password**: Must be `auren_password_2024` (NOT `auren_secure_2025`)
2. **Image**: Must be `auren_deploy_biometric-bridge:latest`
3. **Port**: External 8888 maps to internal 8888
4. **Network**: All services MUST be on `auren-network`

---

## ✅ VERIFICATION STEPS

### 1. Health Check
```bash
curl -s http://localhost:8888/health | jq .
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "redis": true,
    "postgres": true,
    "kafka_producer": true,
    "kafka_consumer": true
  }
}
```

### 2. Test Webhook Endpoint
```bash
curl -X POST http://localhost:8888/webhooks/oura \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "daily_readiness",
    "user_id": "test_user",
    "data": {
      "readiness_score": 85,
      "hrv_balance": 72,
      "body_temperature": 36.5,
      "resting_heart_rate": 52
    }
  }' \
  -s | jq .
```

Expected response:
```json
{
  "status": "success",
  "device_type": "oura",
  "events_processed": 0,
  "events": []
}
```

### 3. Check Logs
```bash
docker logs biometric-production --tail 50
```

Look for:
- No ERROR messages
- "Application startup complete"
- "Uvicorn running on http://0.0.0.0:8888"

---

## 📊 MONITORING DEPLOYMENT (CRITICAL!)

### Deploy Monitoring Stack with CORRECT Configuration:

```bash
# 1. Start Exporters (MUST use these exact commands!)
docker run -d \
  --name auren-node-exporter \
  --network auren-network \
  -p 9100:9100 \
  --restart unless-stopped \
  prom/node-exporter:latest

docker run -d \
  --name auren-redis-exporter \
  --network auren-network \
  -p 9121:9121 \
  -e REDIS_ADDR=auren-redis:6379 \
  --restart unless-stopped \
  oliver006/redis_exporter:latest

docker run -d \
  --name auren-postgres-exporter \
  --network auren-network \
  -p 9187:9187 \
  -e DATA_SOURCE_NAME="postgresql://auren_user:auren_password_2024@auren-postgres:5432/auren_production?sslmode=disable" \
  --restart unless-stopped \
  prometheuscommunity/postgres-exporter:latest

# 2. Create CORRECT Prometheus config
cat > /tmp/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'biometric-api'
    static_configs:
      - targets: ['biometric-production:8888']  # MUST use container name!
    metrics_path: '/metrics'

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['auren-redis-exporter:9121']  # MUST use container name!

  - job_name: 'postgres-exporter'  
    static_configs:
      - targets: ['auren-postgres-exporter:9187']  # MUST use container name!

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['auren-node-exporter:9100']  # MUST use container name!
EOF

# 3. Start Prometheus with CORRECT config
docker run -d \
  --name auren-prometheus \
  --network auren-network \
  -p 9090:9090 \
  -v /tmp/prometheus.yml:/etc/prometheus/prometheus.yml \
  --restart unless-stopped \
  prom/prometheus:latest

# 4. Start Grafana
docker run -d \
  --name auren-grafana \
  --network auren-network \
  -p 3000:3000 \
  --restart unless-stopped \
  grafana/grafana:latest
```

### ⚠️ CRITICAL MONITORING RULES:
1. **MUST use container names** in Prometheus config (NOT IP addresses!)
2. **ALL containers MUST be on auren-network**
3. **PostgreSQL password MUST be auren_password_2024**
4. **Include --restart unless-stopped on ALL containers**

---

## 📦 DOCKER COMPOSE ALTERNATIVE

For production, use this `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    container_name: auren-postgres
    networks:
      - auren-network
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: auren_user
      POSTGRES_PASSWORD: auren_password_2024
      POSTGRES_DB: auren_production
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U auren_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: auren-redis
    networks:
      - auren-network
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  kafka:
    image: bitnami/kafka:3.5
    container_name: auren-kafka
    networks:
      - auren-network
    ports:
      - "9092:9092"
    environment:
      KAFKA_CFG_NODE_ID: 0
      KAFKA_CFG_PROCESS_ROLES: controller,broker
      KAFKA_CFG_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
      KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_CFG_CONTROLLER_QUORUM_VOTERS: 0@kafka:9093
      KAFKA_CFG_CONTROLLER_LISTENER_NAMES: CONTROLLER
    restart: unless-stopped

  biometric-production:
    image: auren_deploy_biometric-bridge:latest
    container_name: biometric-production
    networks:
      - auren-network
    ports:
      - "8888:8888"
    environment:
      POSTGRES_HOST: auren-postgres
      POSTGRES_USER: auren_user
      POSTGRES_PASSWORD: auren_password_2024
      POSTGRES_DB: auren_production
      REDIS_HOST: auren-redis
      KAFKA_BOOTSTRAP_SERVERS: auren-kafka:9092
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ENVIRONMENT: production
      DISABLE_TEST_EVENTS: "false"
    depends_on:
      - postgres
      - redis
      - kafka
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8888/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  auren-network:
    external: true

volumes:
  postgres_data:
  redis_data:
```

Deploy with:
```bash
# Create .env file
echo "OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE" > .env

# Deploy all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

---

## 🔧 TROUBLESHOOTING

### Service Won't Start
```bash
# Check logs
docker logs biometric-production --tail 100

# Common fixes:
# 1. Wrong password - use auren_password_2024
# 2. Network issues - ensure all on auren-network
# 3. Port conflicts - check nothing else on 8888
```

### Database Connection Failed
```bash
# Test connection manually
docker exec -it auren-postgres psql -U auren_user -d auren_production

# If fails, recreate with correct password:
docker stop auren-postgres && docker rm auren-postgres
# Then run create command again with auren_password_2024
```

### Kafka Issues
```bash
# Check Kafka logs
docker logs auren-kafka --tail 50

# Restart if needed
docker restart auren-kafka
```

---

## 🛡️ PRODUCTION BEST PRACTICES

1. **Always use restart policies**: `--restart unless-stopped`
2. **Monitor disk space**: Keep < 80% usage
3. **Regular backups**: PostgreSQL data daily
4. **Log rotation**: Implement log size limits
5. **Health monitoring**: Set up alerts for failed health checks

---

## 📊 MONITORING

### Quick Status Check
```bash
#!/bin/bash
echo "=== AUREN System Status ==="
echo "Services:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "auren|biometric"
echo -e "\nHealth:"
curl -s http://localhost:8888/health | jq -r '.status'
echo -e "\nDisk:"
df -h / | grep -E "Filesystem|/"
```

### Service Logs
```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker logs biometric-production -f
```

---

## 🚫 DO NOT DO THIS

1. **Do NOT** use different PostgreSQL passwords
2. **Do NOT** create new Docker images for minor fixes
3. **Do NOT** run services outside the auren-network
4. **Do NOT** use ports other than documented
5. **Do NOT** mix development and production configs

---

## 📝 MAINTENANCE

### Weekly Tasks
```bash
# Clean unused images
docker image prune -f

# Check disk usage
docker system df

# Backup database
docker exec auren-postgres pg_dump -U auren_user auren_production > backup_$(date +%Y%m%d).sql
```

### Monthly Tasks
```bash
# Full system cleanup (schedule downtime)
docker system prune -a --volumes

# Update base images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

---

*This guide represents the validated, production-ready deployment process for AUREN. Any deviations should be documented and approved.* 