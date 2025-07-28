# NEUROS Deployment Guide

## Deployment Architecture Recommendations

### Current Status
Based on my analysis, **NONE of the biometric bridge sections (1-8) are currently deployed** to the DigitalOcean server. All components exist locally but need production deployment.

### Recommended Architecture: Microservices Approach

#### 1. **Service Architecture**
Deploy the biometric bridge as **multiple coordinated microservices**:

```yaml
services:
  # Section 1-6: Core Biometric Services
  biometric-kafka-consumer:
    image: auren/biometric-kafka-consumer:latest
    environment:
      - KAFKA_BROKERS=kafka:9092
      - CONSUMER_GROUP=biometric-processor
    depends_on:
      - kafka
  
  # Section 7: Bridge Service
  biometric-bridge:
    image: auren/biometric-bridge:latest
    environment:
      - KAFKA_BROKERS=kafka:9092
      - POSTGRES_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
    depends_on:
      - kafka
      - postgres
      - redis
  
  # Section 8: NEUROS Cognitive Graph
  neuros-cognitive-service:
    image: auren/neuros-cognitive:latest
    environment:
      - POSTGRES_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
      - NEUROS_YAML_PATH=/config/neuros_agent_profile.yaml
    volumes:
      - ./neuros_agent_profile.yaml:/config/neuros_agent_profile.yaml:ro
    depends_on:
      - postgres
      - redis
```

#### 2. **Integration Strategy**

**Option A: Unified Service** (Recommended for MVP)
```python
# main.py - Single deployable service
from biometric_bridge import BiometricKafkaLangGraphBridge
from neuros_graph import NEUROSCognitiveGraph

class UnifiedBiometricService:
    def __init__(self):
        self.bridge = BiometricKafkaLangGraphBridge()
        self.neuros = NEUROSCognitiveGraph(
            llm=self.llm,
            postgres_url=os.getenv('POSTGRES_URL'),
            redis_url=os.getenv('REDIS_URL'),
            neuros_yaml_path='/config/neuros_agent_profile.yaml'
        )
        
    async def start(self):
        # Initialize components
        await self.neuros.initialize()
        await self.bridge.initialize(self.neuros)
        
        # Start consuming
        await self.bridge.start_consuming()
```

**Option B: Separate Services** (Recommended for Scale)
- Deploy each section as independent service
- Use Kafka for inter-service communication
- Share state via PostgreSQL/Redis

### Deployment Steps

#### 1. **Create Docker Images**

```dockerfile
# Dockerfile for NEUROS service
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY section_8_neuros_graph.py .
COPY neuros_agent_profile.yaml /config/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. **Deploy to DigitalOcean**

```bash
# 1. Build and push images
docker build -t auren/neuros-cognitive:latest .
docker push auren/neuros-cognitive:latest

# 2. SSH to server
ssh root@144.126.215.218

# 3. Pull and run
docker pull auren/neuros-cognitive:latest
docker-compose up -d neuros-cognitive-service

# 4. Verify deployment
docker logs -f auren-neuros-cognitive-service-1
curl http://localhost:8000/health
```

#### 3. **Connect to Production Infrastructure**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  neuros-cognitive-service:
    image: auren/neuros-cognitive:latest
    environment:
      # Connect to existing infrastructure
      - POSTGRES_URL=postgresql://auren_user:${POSTGRES_PASSWORD}@postgres:5432/auren_production
      - REDIS_URL=redis://redis:6379/0
      - KAFKA_BROKERS=kafka:9092
    networks:
      - auren-network
    deploy:
      replicas: 2  # For high availability
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

### Production Readiness Checklist

#### Environment Variables
```bash
# .env.production
POSTGRES_URL=postgresql://auren_user:xxx@postgres:5432/auren_production
REDIS_URL=redis://redis:6379/0
KAFKA_BROKERS=kafka:9092
NEUROS_YAML_PATH=/config/neuros_agent_profile.yaml
LOG_LEVEL=INFO
SENTRY_DSN=https://xxx@sentry.io/xxx  # For error tracking
```

#### Health Monitoring
```python
# health_check.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "neuros-cognitive",
        "version": "1.0.0",
        "checks": {
            "postgres": await check_postgres(),
            "redis": await check_redis(),
            "kafka": await check_kafka()
        }
    }
```

#### Logging & Monitoring
```yaml
# Add to docker-compose
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service=neuros"
```

### Deployment Commands

```bash
# Full deployment sequence
cd /path/to/auren

# 1. Build all images
make build-production

# 2. Deploy to server
make deploy-production

# 3. Run migrations
make migrate-production

# 4. Start services
ssh root@144.126.215.218 "cd /opt/auren && docker-compose up -d"

# 5. Monitor logs
ssh root@144.126.215.218 "docker logs -f auren-neuros-cognitive-service-1"
```

### Service Dependencies

1. **Kafka** (Already running) - Event streaming
2. **PostgreSQL/TimescaleDB** (Already running) - State persistence
3. **Redis** (Already running) - Hot memory tier
4. **Nginx** (Already running) - Reverse proxy

### API Endpoints

Once deployed, NEUROS will be available at:

- **Health Check**: `http://aupex.ai/api/neuros/health`
- **Process Event**: `POST http://aupex.ai/api/neuros/process`
- **Get State**: `GET http://aupex.ai/api/neuros/state/{thread_id}`
- **WebSocket**: `ws://aupex.ai/api/neuros/ws/{thread_id}`

### Next Steps

1. **Immediate**: Package Section 8 as Docker container
2. **Tomorrow**: Deploy to staging environment
3. **This Week**: Connect real biometric streams
4. **Next Sprint**: Scale to handle 10,000 users

---

## Quick Start

```bash
# Clone and prepare
git clone https://github.com/auren/neuros
cd neuros

# Build
docker build -t auren/neuros-cognitive:latest .

# Deploy
docker push auren/neuros-cognitive:latest
ssh root@144.126.215.218 "docker pull auren/neuros-cognitive:latest && docker run -d auren/neuros-cognitive:latest"
```

Ready for production! 🚀 