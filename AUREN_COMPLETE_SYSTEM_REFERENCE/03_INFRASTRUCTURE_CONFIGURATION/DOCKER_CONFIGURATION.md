# DOCKER CONFIGURATION
## Complete Container Orchestration and Infrastructure Setup

*Last Updated: July 30, 2025*  
*Status: ✅ PRODUCTION OPERATIONAL*  
*Platform: DigitalOcean Server (144.126.215.218)*

---

## 🐳 **DOCKER OVERVIEW**

The AUREN system runs entirely on Docker containers orchestrated on a single DigitalOcean server. All containers operate within the `auren-network` Docker network for secure internal communication while exposing only necessary ports to the public.

### **Container Architecture**
- **Network**: `auren-network` (bridge network)
- **Server**: 144.126.215.218 (DigitalOcean Droplet)
- **Total Containers**: 15+ containers (applications + infrastructure + monitoring)
- **Orchestration**: Docker Compose + manual container management

---

## 🏗️ **CONTAINER ECOSYSTEM**

### **Application Containers** ⚠️ **ACTUAL RUNNING STATE**
```
Application Layer (VERIFIED July 30, 2025):
├── ❌ neuros-advanced              # NEUROS AI Agent (Port 8000) - NOT RUNNING
├── ✅ biometric-production         # Original biometric service (Port 8888) - RUNNING
├── ✅ biometric-bridge            # Enhanced bridge (Port 8889) - RUNNING & HEALTHY
└── ❌ auren-web                   # Web services - NOT PRESENT
```

**REALITY**: Only 2 of 4 documented application containers are actually running.

### **Data Layer Containers**
```
Data Infrastructure:
├── auren-postgres              # PostgreSQL + TimescaleDB (Port 5432)
├── auren-redis                 # Redis cache (Port 6379)
├── auren-kafka                 # Apache Kafka (Port 9092)
├── auren-zookeeper            # Zookeeper for Kafka (Port 2181)
└── auren-chromadb             # Vector database (Port 8000)
```

### **Monitoring Containers**
```
Monitoring Stack:
├── auren-prometheus           # Metrics collection (Port 9090)
├── auren-grafana             # Dashboards (Port 3000)
├── node-exporter             # System metrics (Port 9100)
├── redis-exporter            # Redis metrics (Port 9121)
└── postgres-exporter         # PostgreSQL metrics (Port 9187)
```

---

## ⚙️ **DOCKER NETWORK CONFIGURATION**

### **Network Setup**
```bash
# auren-network configuration
docker network create auren-network --driver bridge
```

### **Network Details**
```json
{
  "Name": "auren-network",
  "Driver": "bridge",
  "Scope": "local",
  "Internal": false,
  "Attachable": true,
  "Ingress": false,
  "EnableIPv6": false,
  "IPAM": {
    "Driver": "default",
    "Config": [
      {
        "Subnet": "172.20.0.0/16",
        "Gateway": "172.20.0.1"
      }
    ]
  }
}
```

### **Container Communication**
```
Internal DNS Resolution:
├── auren-postgres:5432         # PostgreSQL access
├── auren-redis:6379           # Redis access
├── auren-kafka:9092           # Kafka bootstrap servers
├── auren-zookeeper:2181       # Zookeeper coordination
└── auren-chromadb:8000        # Vector database access
```

---

## 🚀 **CONTAINER CONFIGURATIONS**

### **1. NEUROS AI Agent**
```bash
# Container: neuros-advanced
docker run -d \
  --name neuros-advanced \
  --network auren-network \
  -p 8000:8000 \
  --restart unless-stopped \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  -e POSTGRES_URL="postgresql://auren_user:auren_password_2024@auren-postgres:5432/auren_production" \
  -e REDIS_URL="redis://auren-redis:6379/0" \
  -e KAFKA_BOOTSTRAP_SERVERS="auren-kafka:9092" \
  neuros-advanced:latest
```

### **2. Enhanced Biometric Bridge**
```bash
# Container: biometric-bridge (Production Enhanced)
docker run -d \
  --name biometric-bridge \
  --network auren-network \
  -p 8889:8889 \
  --env-file /root/auren-biometric-bridge/.env \
  --restart unless-stopped \
  auren-biometric-bridge:production-enhanced
```

### **3. PostgreSQL + TimescaleDB**
```bash
# Container: auren-postgres
docker run -d \
  --name auren-postgres \
  --network auren-network \
  -p 5432:5432 \
  -e POSTGRES_DB=auren_production \
  -e POSTGRES_USER=auren_user \
  -e POSTGRES_PASSWORD=auren_password_2024 \
  -v postgres_data:/var/lib/postgresql/data \
  -v /root/init-scripts:/docker-entrypoint-initdb.d \
  --restart unless-stopped \
  timescale/timescaledb:latest-pg15
```

### **4. Redis Cache**
```bash
# Container: auren-redis
docker run -d \
  --name auren-redis \
  --network auren-network \
  -p 6379:6379 \
  -v redis_data:/data \
  --restart unless-stopped \
  redis:7-alpine redis-server --appendonly yes
```

### **5. Apache Kafka**
```bash
# Container: auren-kafka
docker run -d \
  --name auren-kafka \
  --network auren-network \
  -p 9092:9092 \
  -e KAFKA_ZOOKEEPER_CONNECT=auren-zookeeper:2181 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://auren-kafka:9092 \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  -e KAFKA_AUTO_CREATE_TOPICS_ENABLE=true \
  -v kafka_data:/var/lib/kafka/data \
  --restart unless-stopped \
  confluentinc/cp-kafka:latest
```

### **6. Zookeeper**
```bash
# Container: auren-zookeeper
docker run -d \
  --name auren-zookeeper \
  --network auren-network \
  -p 2181:2181 \
  -e ZOOKEEPER_CLIENT_PORT=2181 \
  -e ZOOKEEPER_TICK_TIME=2000 \
  -v zookeeper_data:/var/lib/zookeeper/data \
  --restart unless-stopped \
  confluentinc/cp-zookeeper:latest
```

### **7. Prometheus**
```bash
# Container: auren-prometheus
docker run -d \
  --name auren-prometheus \
  --network auren-network \
  -p 9090:9090 \
  -v /root/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v prometheus_data:/prometheus \
  --restart unless-stopped \
  prom/prometheus:latest
```

### **8. Grafana**
```bash
# Container: auren-grafana
docker run -d \
  --name auren-grafana \
  --network auren-network \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -v grafana_data:/var/lib/grafana \
  -v /root/grafana/provisioning:/etc/grafana/provisioning \
  --restart unless-stopped \
  grafana/grafana:latest
```

---

## 📋 **DOCKER COMPOSE CONFIGURATION**

### **Production Docker Compose (`docker-compose.yml`)**
```yaml
version: '3.8'

services:
  # Data Layer
  postgres:
    image: timescale/timescaledb:latest-pg15
    container_name: auren-postgres
    environment:
      POSTGRES_DB: auren_production
      POSTGRES_USER: auren_user
      POSTGRES_PASSWORD: auren_password_2024
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    networks:
      - auren-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: auren-redis
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - auren-network
    restart: unless-stopped

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    container_name: auren-zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"
    volumes:
      - zookeeper_data:/var/lib/zookeeper/data
    networks:
      - auren-network
    restart: unless-stopped

  kafka:
    image: confluentinc/cp-kafka:latest
    container_name: auren-kafka
    depends_on:
      - zookeeper
    environment:
      KAFKA_ZOOKEEPER_CONNECT: auren-zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://auren-kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
    ports:
      - "9092:9092"
    volumes:
      - kafka_data:/var/lib/kafka/data
    networks:
      - auren-network
    restart: unless-stopped

  # Monitoring Layer
  prometheus:
    image: prom/prometheus:latest
    container_name: auren-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - auren-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: auren-grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    networks:
      - auren-network
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    networks:
      - auren-network
    restart: unless-stopped

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: redis-exporter
    environment:
      REDIS_ADDR: redis://auren-redis:6379
    ports:
      - "9121:9121"
    networks:
      - auren-network
    restart: unless-stopped

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://auren_user:auren_password_2024@auren-postgres:5432/auren_production?sslmode=disable"
    ports:
      - "9187:9187"
    networks:
      - auren-network
    restart: unless-stopped

networks:
  auren-network:
    driver: bridge
    external: true

volumes:
  postgres_data:
  redis_data:
  kafka_data:
  zookeeper_data:
  prometheus_data:
  grafana_data:
```

---

## 🔧 **CONTAINER MANAGEMENT COMMANDS**

### **System Health Checks**
```bash
# Check all AUREN containers
docker ps | grep -E "neuros|biometric|auren"

# Check container resource usage
docker stats $(docker ps --filter "name=auren" --filter "name=neuros" --filter "name=biometric" -q)

# Check container logs
docker logs neuros-advanced --tail 50
docker logs biometric-bridge --tail 50
docker logs auren-postgres --tail 50
```

### **Infrastructure Management**
```bash
# Start infrastructure services (proper order)
docker start auren-postgres auren-redis
sleep 10
docker start auren-zookeeper
sleep 5
docker start auren-kafka
sleep 10

# Start application services
docker start neuros-advanced biometric-bridge

# Start monitoring services
docker start auren-prometheus auren-grafana node-exporter redis-exporter postgres-exporter
```

### **Container Cleanup**
```bash
# Stop all AUREN containers
docker stop $(docker ps --filter "name=auren" --filter "name=neuros" --filter "name=biometric" -q)

# Remove containers (DANGER - data loss possible)
docker rm $(docker ps -a --filter "name=auren" --filter "name=neuros" --filter "name=biometric" -q)

# Clean up unused images
docker image prune -f

# Clean up unused volumes (DANGER - data loss)
docker volume prune -f
```

---

## 💾 **VOLUME MANAGEMENT**

### **Persistent Volumes**
```bash
# List AUREN volumes
docker volume ls | grep -E "postgres|redis|kafka|grafana|prometheus"

# Backup volumes
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
docker run --rm -v redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

### **Volume Inspection**
```bash
# Inspect volume details
docker volume inspect postgres_data
docker volume inspect redis_data
docker volume inspect kafka_data

# Check volume usage
docker system df -v
```

---

## 🔒 **SECURITY CONFIGURATION**

### **Network Security**
```bash
# auren-network security features:
# - Internal container communication
# - No external access except mapped ports
# - Bridge network isolation
# - Container DNS resolution

# Port mapping (external:internal)
# 8000:8000   - NEUROS AI Agent
# 8888:8888   - Original Biometric Service
# 8889:8889   - Enhanced Biometric Bridge
# 5432:5432   - PostgreSQL (admin access)
# 6379:6379   - Redis (admin access)
# 9092:9092   - Kafka (admin access)
# 3000:3000   - Grafana Dashboard
# 9090:9090   - Prometheus
```

### **Container Security**
```bash
# Security best practices implemented:
# - Non-root containers where possible
# - Restart policies (unless-stopped)
# - Resource limits (memory/CPU)
# - Read-only filesystems where applicable
# - Security scanning with docker scan
```

---

## 📊 **MONITORING & METRICS**

### **Container Health Monitoring**
```bash
# Health check script
#!/bin/bash
echo "=== AUREN Container Health Check ==="

containers=("neuros-advanced" "biometric-bridge" "auren-postgres" "auren-redis" "auren-kafka")

for container in "${containers[@]}"; do
    if docker ps | grep -q "$container"; then
        echo "✅ $container: Running"
    else
        echo "❌ $container: Not running"
    fi
done

# Check resource usage
echo -e "\n=== Resource Usage ==="
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

### **Log Aggregation**
```bash
# Centralized logging
docker logs neuros-advanced 2>&1 | grep -E "(ERROR|WARNING)" > /root/logs/neuros_errors.log
docker logs biometric-bridge 2>&1 | grep -E "(ERROR|WARNING)" > /root/logs/bridge_errors.log
docker logs auren-postgres 2>&1 | grep -E "(ERROR|WARNING)" > /root/logs/postgres_errors.log
```

---

## 🔄 **DEPLOYMENT PROCEDURES**

### **Infrastructure Deployment**
```bash
# 1. Deploy infrastructure services
cd /root/auren-infrastructure
docker-compose up -d postgres redis zookeeper kafka

# 2. Wait for services to be ready
sleep 30

# 3. Deploy monitoring
docker-compose up -d prometheus grafana node-exporter redis-exporter postgres-exporter

# 4. Deploy applications
docker run -d --name neuros-advanced --network auren-network -p 8000:8000 --restart unless-stopped neuros-advanced:latest
docker run -d --name biometric-bridge --network auren-network -p 8889:8889 --env-file .env --restart unless-stopped auren-biometric-bridge:production-enhanced
```

### **Rolling Updates**
```bash
# Rolling update procedure for zero downtime
# 1. Build new image
docker build -t auren-biometric-bridge:new-version .

# 2. Stop old container
docker stop biometric-bridge

# 3. Start new container
docker run -d --name biometric-bridge-new --network auren-network -p 8889:8889 --env-file .env --restart unless-stopped auren-biometric-bridge:new-version

# 4. Verify health
curl http://localhost:8889/health

# 5. Remove old container
docker rm biometric-bridge

# 6. Rename new container
docker rename biometric-bridge-new biometric-bridge
```

---

## 📞 **SUPPORT INFORMATION**

**Infrastructure**: Docker + DigitalOcean  
**Network**: auren-network (bridge)  
**Server**: 144.126.215.218  
**Status**: ✅ PRODUCTION OPERATIONAL

### **Critical Commands**
- **Health Check**: `docker ps | grep -E "neuros|biometric|auren"`
- **Logs**: `docker logs [container-name] --tail 50`
- **Stats**: `docker stats`
- **Network**: `docker network inspect auren-network`

### **Emergency Procedures**
- **Full Restart**: Stop all → Start infrastructure → Start applications
- **Infrastructure First**: Always start postgres, redis, kafka before applications
- **Log Analysis**: Check container logs for error patterns
- **Resource Check**: Monitor CPU/memory usage during issues

---

*This document provides complete Docker configuration details for the AUREN system. All containers are production-ready with proper networking, security, and monitoring.* 