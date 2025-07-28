# DOCKER SERVICES DOCUMENTATION

## Detailed Documentation for All Containerized Services

---

## 📋 Service Overview

| Service | Container Name | Port | Purpose | Status |
|---------|---------------|------|---------|--------|
| PostgreSQL | auren-postgres | 5432 | Primary database | Essential |
| Redis | auren-redis | 6379 | Cache & hot memory | Essential |
| ChromaDB | auren-chromadb | 8000 | Vector search | Essential |
| AUREN API | auren-api | 8080 | Backend API | Essential |
| Nginx | auren-nginx | 80/443 | Web server | Essential |
| Zookeeper | auren-zookeeper | 2181 | Kafka coordination | Running |
| Kafka | auren-kafka | 9092 | Event streaming | Running |
| Kafka UI | auren-kafka-ui | 8081 | Kafka monitoring | Running |
| Biometric Bridge | auren-biometric-bridge | 8002 | LangGraph service | New |

---

## 🐘 PostgreSQL (TimescaleDB)

### Configuration
```yaml
postgres:
  image: timescale/timescaledb:latest-pg16
  container_name: auren-postgres
  ports:
    - "5432:5432"
  environment:
    POSTGRES_DB: auren_db
    POSTGRES_USER: auren_user
    POSTGRES_PASSWORD: auren_password_2024
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./sql/init:/docker-entrypoint-initdb.d
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U auren_user -d auren_db"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Key Features
- **TimescaleDB Extension**: Time-series optimized for biometric data
- **Version**: PostgreSQL 16 with TimescaleDB
- **Memory**: ~800MB typical usage
- **Storage**: Growing at ~1GB/week

### Database Schema
```sql
Tables:
- events (event sourcing)
- agent_memories (warm tier storage)
- hypotheses (agent insights)
- learning_progress (adaptation tracking)
- biometric_events (time-series)
- neuros_checkpoints (LangGraph state)
```

### Optimization
- Configured indexes for memory access patterns
- Connection pooling enabled
- Autovacuum tuned for performance
- WAL archiving for point-in-time recovery

### Maintenance
```bash
# Backup database
docker exec auren-postgres pg_dump -U auren_user auren_db > backup.sql

# Restore database
docker exec -i auren-postgres psql -U auren_user auren_db < backup.sql

# Check size
docker exec auren-postgres psql -U auren_user -d auren_db -c "SELECT pg_database_size('auren_db');"
```

---

## 🚀 Redis

### Configuration
```yaml
redis:
  image: redis:7-alpine
  container_name: auren-redis
  ports:
    - "6379:6379"
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Key Features
- **Version**: Redis 7 Alpine (minimal footprint)
- **Persistence**: AOF enabled
- **Memory**: ~200MB typical usage
- **Performance**: 5000+ ops/sec

### Data Structure
```
Keys:
- agent:{agent_id}:memory:{memory_id} (hot memories)
- session:{session_id}:state (user sessions)
- cache:{endpoint}:{params} (API cache)
- checkpoint:{thread_id} (LangGraph checkpoints)
```

### Commands
```bash
# Check memory usage
docker exec auren-redis redis-cli INFO memory

# Monitor real-time commands
docker exec auren-redis redis-cli MONITOR

# Flush cache (careful!)
docker exec auren-redis redis-cli FLUSHALL
```

---

## 🔍 ChromaDB

### Configuration
```yaml
chromadb:
  image: chromadb/chroma:0.4.22
  container_name: auren-chromadb
  ports:
    - "8000:8000"
  environment:
    - IS_PERSISTENT=TRUE
    - ANONYMIZED_TELEMETRY=FALSE
  restart: unless-stopped
```

### Key Features
- **Version**: ChromaDB 0.4.22
- **Purpose**: Vector embeddings for semantic search
- **Memory**: ~600MB typical usage
- **Storage**: Growing with knowledge base

### Collections
```
Collections:
- agent_knowledge (agent-specific embeddings)
- conversation_history (semantic search)
- protocol_library (medical protocols)
- research_papers (scientific literature)
```

### API Usage
```python
# Add embedding
POST http://localhost:8000/api/v1/collections/{collection}/add
{
  "embeddings": [[0.1, 0.2, ...]],
  "documents": ["text"],
  "metadatas": [{"source": "agent"}],
  "ids": ["unique_id"]
}

# Query
POST http://localhost:8000/api/v1/collections/{collection}/query
{
  "query_embeddings": [[0.1, 0.2, ...]],
  "n_results": 10
}
```

---

## 🔧 AUREN API

### Configuration
```yaml
auren-api:
  build:
    context: .
    dockerfile: Dockerfile.api
  container_name: auren-api
  ports:
    - "8080:8080"
  environment:
    - DATABASE_URL=postgresql://auren_user:auren_password_2024@postgres:5432/auren_db
    - REDIS_URL=redis://redis:6379
    - CHROMADB_HOST=chromadb
    - CHROMADB_PORT=8000
    - PYTHONPATH=/app
    - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  volumes:
    - ./auren:/app/auren
  command: python -m uvicorn auren.api.dashboard_api_minimal:app --host 0.0.0.0 --port 8080
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
```

### Key Features
- **Framework**: FastAPI
- **Async**: Full async/await support
- **Memory**: ~400MB typical usage
- **Endpoints**: 15+ API endpoints

### Main Endpoints
```
GET  /health                     # Health check
GET  /api/memory/stats          # Memory statistics
GET  /api/knowledge-graph/data  # Knowledge visualization
POST /api/protocols/{protocol}/entry  # Protocol entries
POST /api/biometric/analyze     # Biometric analysis
WS   /ws/dashboard/{user_id}    # Real-time updates
```

### Monitoring
```bash
# View logs
docker logs -f auren-api

# Check health
curl http://localhost:8080/health

# API metrics
curl http://localhost:8080/metrics
```

---

## 🌐 Nginx

### Configuration
```yaml
nginx:
  image: nginx:alpine
  container_name: auren-nginx
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx-temp.conf:/etc/nginx/nginx.conf:ro
    - ./auren/dashboard_v2:/usr/share/nginx/html:ro
    - nginx-logs:/var/log/nginx
  depends_on:
    - auren-api
  restart: unless-stopped
```

### Key Features
- **Version**: Nginx Alpine
- **Purpose**: Reverse proxy + static files
- **Memory**: ~100MB usage
- **Performance**: 10k+ requests/sec

### Configuration Highlights
```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# Proxy settings
location /api/ {
    proxy_pass http://auren-api:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# WebSocket support
location /ws {
    proxy_pass http://auren-api:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

## 📊 Kafka Ecosystem

### Zookeeper Configuration
```yaml
zookeeper:
  image: confluentinc/cp-zookeeper:7.5.0
  container_name: auren-zookeeper
  environment:
    ZOOKEEPER_CLIENT_PORT: 2181
    ZOOKEEPER_TICK_TIME: 2000
```

### Kafka Configuration
```yaml
kafka:
  image: confluentinc/cp-kafka:7.5.0
  container_name: auren-kafka
  ports:
    - "9092:9092"
    - "29092:29092"
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
```

### Kafka UI Configuration
```yaml
kafka-ui:
  image: provectuslabs/kafka-ui:latest
  container_name: auren-kafka-ui
  ports:
    - "8081:8080"
  environment:
    KAFKA_CLUSTERS_0_NAME: auren
    KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:29092
```

### Topics
```
Topics:
- biometric-events (biometric data stream)
- neuros-mode-switches (cognitive mode changes)
- agent-communications (inter-agent messages)
- system-events (audit trail)
```

### Management
```bash
# List topics
docker exec auren-kafka kafka-topics --list --bootstrap-server localhost:9092

# Create topic
docker exec auren-kafka kafka-topics --create --topic test --bootstrap-server localhost:9092

# View messages
docker exec auren-kafka kafka-console-consumer --topic biometric-events --from-beginning --bootstrap-server localhost:9092
```

---

## 🧬 Biometric Bridge (New)

### Configuration
```yaml
biometric-bridge:
  build:
    context: .
    dockerfile: Dockerfile.api
  container_name: auren-biometric-bridge
  environment:
    - POSTGRES_URL=postgresql://auren_user:auren_password_2024@postgres:5432/auren_db
    - REDIS_URL=redis://redis:6379
    - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
    - WEBSOCKET_URL=ws://auren-api:8080/ws
    - OPENAI_API_KEY=${OPENAI_API_KEY}
  depends_on:
    - postgres
    - redis
    - kafka
    - auren-api
  volumes:
    - ./auren:/app/auren
  command: python -m auren.biometric.bridge
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8002/metrics"]
```

### Key Features
- **Purpose**: LangGraph biometric processing
- **Framework**: LangGraph + Kafka consumer
- **Memory**: ~300MB usage
- **Processing**: Real-time biometric events

### Cognitive Modes
```
Modes:
- reflex (immediate response)
- pattern (pattern recognition)
- hypothesis (deep analysis)
- guardian (safety override)
```

---

## 🔄 Service Dependencies

### Startup Order
```
1. postgres (database must be ready)
2. redis (cache must be available)
3. chromadb (can start independently)
4. zookeeper (kafka dependency)
5. kafka (after zookeeper)
6. auren-api (after postgres, redis, chromadb)
7. nginx (after auren-api)
8. kafka-ui (after kafka)
9. biometric-bridge (after all core services)
```

### Health Check Chain
```
postgres healthy → redis healthy → auren-api healthy → nginx starts
                                                     → biometric-bridge starts
```

---

## 📊 Resource Management

### Memory Limits (Recommended)
```yaml
deploy:
  resources:
    limits:
      memory: 800M  # postgres
      memory: 300M  # redis
      memory: 600M  # chromadb
      memory: 500M  # auren-api
      memory: 200M  # nginx
      memory: 800M  # kafka
```

### CPU Limits (Optional)
```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'  # Limit to half a CPU
```

---

## 🛠️ Common Operations

### View All Services
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Restart Specific Service
```bash
docker-compose -f docker-compose.prod.yml restart [service-name]
```

### Update Service Image
```bash
docker-compose -f docker-compose.prod.yml pull [service-name]
docker-compose -f docker-compose.prod.yml up -d [service-name]
```

### Scale Service (if stateless)
```bash
docker-compose -f docker-compose.prod.yml up -d --scale auren-api=3
```

### Remove Everything
```bash
docker-compose -f docker-compose.prod.yml down -v
```

---

## 🔍 Debugging Services

### Check Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f [service-name]

# Last 100 lines
docker-compose logs --tail 100 [service-name]
```

### Enter Container
```bash
docker exec -it [container-name] /bin/sh
```

### Check Resource Usage
```bash
docker stats
```

### Network Debugging
```bash
# List networks
docker network ls

# Inspect network
docker network inspect auren-network

# Test connectivity
docker exec auren-api ping postgres
```

---

*Each service is designed to be resilient, scalable, and maintainable. Regular monitoring and maintenance ensure optimal performance.* 