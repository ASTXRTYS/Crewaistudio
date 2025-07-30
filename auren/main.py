# =============================================================================
# SECTION 12: MAIN EXECUTION WITH DOCKER SUPPORT (PRODUCTION HARDENED)
# =============================================================================
# Purpose: Production-ready runtime with proper async handling, graceful shutdown,
# security hardening, and comprehensive deployment stack
# Last Updated: 2025-01-29
# =============================================================================

import asyncio
import json
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

import asyncpg
import redis.asyncio as aioredis  # Fixed: Using async Redis
import uvicorn
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer  # Fixed: Proper async Kafka
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential  # Added: Retry logic

# Import our components
from biometric.bridge import BiometricKafkaLangGraphBridge
from agents.neuros.section_8_neuros_graph import NEUROSCognitiveGraph
from security import create_security_app  # Section 9 security integration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# GLOBAL STATE MANAGEMENT
# =============================================================================

class AppState:
    """Centralized state management for graceful shutdown"""
    def __init__(self):
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[aioredis.Redis] = None
        self.kafka_producer: Optional[AIOKafkaProducer] = None
        self.kafka_consumer: Optional[AIOKafkaConsumer] = None
        self.bridge: Optional[BiometricKafkaLangGraphBridge] = None
        self.neuros: Optional[NEUROSCognitiveGraph] = None
        self.shutdown_event = asyncio.Event()
        
app_state = AppState()

# =============================================================================
# LIFESPAN MANAGEMENT
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle with proper startup and shutdown
    """
    # Startup
    logger.info("🚀 Starting AUREN Biometric Bridge System...")
    logger.info("The World's First Biometric-Aware Cognitive AI")
    
    try:
        # Initialize connections with retry
        app_state.postgres_pool = await create_postgres_pool()
        app_state.redis_client = await create_redis_client()
        
        if os.getenv("RUN_MODE") == "consumer":
            # Initialize Kafka consumer components
            app_state.kafka_consumer = await create_kafka_consumer()
            app_state.kafka_producer = await create_kafka_producer()
            
            # Initialize NEUROS
            app_state.neuros = await create_neuros()
            
            # Initialize bridge
            app_state.bridge = BiometricKafkaLangGraphBridge(
                graph=app_state.neuros.graph,
                kafka_consumer=app_state.kafka_consumer,
                kafka_producer=app_state.kafka_producer,
                postgres_pool=app_state.postgres_pool,
                redis_client=app_state.redis_client
            )
            
            # Start consuming in background
            asyncio.create_task(consume_biometric_events())
        
        logger.info("✅ All systems initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Initiating graceful shutdown...")
    
    # Signal shutdown to all components
    app_state.shutdown_event.set()
    
    # Close connections in order
    if app_state.bridge:
        await app_state.bridge.stop_consuming()
    
    if app_state.kafka_consumer:
        await app_state.kafka_consumer.stop()
    
    if app_state.kafka_producer:
        await app_state.kafka_producer.stop()
    
    if app_state.redis_client:
        await app_state.redis_client.close()
    
    if app_state.postgres_pool:
        await app_state.postgres_pool.close()
    
    logger.info("✅ Graceful shutdown complete")

# =============================================================================
# CONNECTION FACTORIES WITH RETRY
# =============================================================================

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    reraise=True
)
async def create_postgres_pool() -> asyncpg.Pool:
    """Create PostgreSQL connection pool with retry logic"""
    logger.info("Connecting to PostgreSQL...")
    
    pool = await asyncpg.create_pool(
        os.getenv("POSTGRES_URL"),
        min_size=5,
        max_size=20,
        command_timeout=60
    )
    
    # Test connection
    async with pool.acquire() as conn:
        version = await conn.fetchval("SELECT version()")
        logger.info(f"Connected to PostgreSQL: {version}")
    
    return pool

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=30),
    reraise=True
)
async def create_redis_client() -> aioredis.Redis:
    """Create Redis client with retry logic"""
    logger.info("Connecting to Redis...")
    
    client = await aioredis.from_url(
        os.getenv("REDIS_URL"),
        encoding="utf-8",
        decode_responses=True,
        health_check_interval=30
    )
    
    # Test connection
    await client.ping()
    logger.info("Connected to Redis")
    
    return client

async def create_kafka_consumer() -> AIOKafkaConsumer:
    """Create Kafka consumer with proper configuration"""
    consumer = AIOKafkaConsumer(
        'biometric-events',         # From enterprise bridge (Oura, WHOOP, Apple)
        'terra-biometric-events',   # From Terra direct Kafka integration
        'health-events',
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS").split(","),
        group_id='neuros-cognitive-processor',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        enable_auto_commit=False,
        auto_offset_reset='earliest',
        max_poll_records=100
    )
    
    await consumer.start()
    logger.info("Kafka consumer started")
    return consumer

async def create_kafka_producer() -> AIOKafkaProducer:
    """Create Kafka producer with proper configuration"""
    producer = AIOKafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS").split(","),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        compression_type='gzip',
        acks='all'
    )
    
    await producer.start()
    logger.info("Kafka producer started")
    return producer

async def create_neuros() -> NEUROSCognitiveGraph:
    """Create NEUROS cognitive graph with proper API key handling"""
    # Fixed: Pass API key explicitly
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")  # Fixed: Explicit API key
    )
    
    neuros = NEUROSCognitiveGraph(
        llm=llm,
        postgres_url=os.getenv("POSTGRES_URL"),
        redis_url=os.getenv("REDIS_URL")
    )
    
    await neuros.initialize()
    logger.info("NEUROS cognitive graph initialized")
    return neuros

# =============================================================================
# BACKGROUND TASKS
# =============================================================================

async def consume_biometric_events():
    """Background task for consuming Kafka events"""
    logger.info("Starting biometric event consumption...")
    
    try:
        while not app_state.shutdown_event.is_set():
            try:
                # Process events with timeout
                await asyncio.wait_for(
                    app_state.bridge.process_batch(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.debug("No events received in 30s, continuing...")
            except Exception as e:
                logger.error(f"Error processing events: {e}")
                await asyncio.sleep(5)  # Back off on error
                
    except asyncio.CancelledError:
        logger.info("Event consumption cancelled")
        raise

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

# Create base app
app = FastAPI(
    title="AUREN Biometric Bridge",
    description="World's First Biometric-Aware Cognitive AI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Integrate Section 9 security (if enabled)
if os.getenv("ENABLE_SECURITY", "true").lower() == "true":
    # Will pass Redis client during lifespan startup
    app = create_security_app(app)

# =============================================================================
# HEALTH & MONITORING ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "mode": os.getenv("RUN_MODE", "api"),
        "components": {}
    }
    
    # Check PostgreSQL
    try:
        if app_state.postgres_pool:
            async with app_state.postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                health_status["components"]["postgres"] = "healthy"
        else:
            health_status["components"]["postgres"] = "not_initialized"
    except Exception as e:
        health_status["components"]["postgres"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        if app_state.redis_client:
            await app_state.redis_client.ping()
            health_status["components"]["redis"] = "healthy"
        else:
            health_status["components"]["redis"] = "not_initialized"
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Kafka (if in consumer mode)
    if os.getenv("RUN_MODE") == "consumer":
        health_status["components"]["kafka_consumer"] = (
            "healthy" if app_state.kafka_consumer else "not_initialized"
        )
        health_status["components"]["kafka_producer"] = (
            "healthy" if app_state.kafka_producer else "not_initialized"
        )
    
    return health_status

@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    metrics_data = []
    
    # Add basic metrics
    if app_state.postgres_pool:
        pool_size = app_state.postgres_pool.get_size()
        pool_free = app_state.postgres_pool.get_idle_size()
        metrics_data.append(f'postgres_pool_size {{}} {pool_size}')
        metrics_data.append(f'postgres_pool_free {{}} {pool_free}')
    
    # Add custom metrics here
    
    return JSONResponse(
        content="\n".join(metrics_data),
        media_type="text/plain"
    )

@app.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe"""
    # Check if all required components are initialized
    if os.getenv("RUN_MODE") == "api":
        ready = app_state.postgres_pool is not None and app_state.redis_client is not None
    else:
        ready = all([
            app_state.postgres_pool,
            app_state.redis_client,
            app_state.kafka_consumer,
            app_state.kafka_producer,
            app_state.neuros,
            app_state.bridge
        ])
    
    if ready:
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Not ready")

# =============================================================================
# SIGNAL HANDLERS
# =============================================================================

def handle_signal(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}")
    app_state.shutdown_event.set()

# Register signal handlers
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """
    Main execution function with comprehensive initialization
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Validate required environment variables
        required_vars = [
            "REDIS_URL",
            "KAFKA_BOOTSTRAP_SERVERS", 
            "POSTGRES_URL",
            "OPENAI_API_KEY"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            logger.info("Please check your .env file or environment configuration")
            sys.exit(1)
        
        # Check run mode
        run_mode = os.getenv("RUN_MODE", "api")
        
        if run_mode == "api":
            # Run as FastAPI server
            logger.info("Starting in API mode...")
            
            config = uvicorn.Config(
                "main:app",  # Consistent with Dockerfile
                host="0.0.0.0",
                port=int(os.getenv("API_PORT", "8000")),
                log_level="info",
                access_log=True,
                loop="uvloop"  # Performance optimization
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        else:
            # Run as standalone consumer
            logger.info("Starting in consumer mode...")
            
            # The lifespan context manager handles initialization
            async with lifespan(app):
                # Wait for shutdown signal
                await app_state.shutdown_event.wait()
                
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# =============================================================================
# DOCKERFILE (PRODUCTION HARDENED)
# =============================================================================

DOCKERFILE_CONTENT = """
# Multi-stage build for security and size optimization
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user early
RUN useradd -m -u 1000 auren

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 auren

# Copy installed packages from builder
COPY --from=builder --chown=auren:auren /root/.local /home/auren/.local

# Set up app directory
WORKDIR /app
COPY --chown=auren:auren . .

# Switch to non-root user
USER auren

# Add local bin to PATH
ENV PATH=/home/auren/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default to API mode
ENV RUN_MODE=api

# Expose API port
EXPOSE 8000

# Health check with proper endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use consistent startup method
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# =============================================================================
# DOCKER COMPOSE (PRODUCTION READY)
# =============================================================================

DOCKER_COMPOSE_CONTENT = """
version: '3.8'

services:
  # PostgreSQL with TimescaleDB
  timescaledb:
    image: timescale/timescaledb:latest-pg16
    restart: unless-stopped
    environment:
      POSTGRES_DB: auren_biometric
      POSTGRES_USER: auren
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secure_password}
      POSTGRES_INITDB_ARGS: "-c shared_preload_libraries=timescaledb"
    volumes:
      - timescale_data:/var/lib/postgresql/data
      - ./sql/init:/docker-entrypoint-initdb.d:ro
    networks:
      - auren-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U auren -d auren_biometric"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    # Remove ports in production, access via network only
    # ports:
    #   - "127.0.0.1:5432:5432"

  # Redis with persistence
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: >
      redis-server
      --appendonly yes
      --appendfsync everysec
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - auren-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    # Remove ports in production
    # ports:
    #   - "127.0.0.1:6379:6379"

  # Kafka with Zookeeper
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    restart: unless-stopped
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
      ZOOKEEPER_INIT_LIMIT: 5
      ZOOKEEPER_SYNC_LIMIT: 2
    volumes:
      - zookeeper_data:/var/lib/zookeeper/data
      - zookeeper_logs:/var/lib/zookeeper/log
    networks:
      - auren-network
    healthcheck:
      test: ["CMD", "bash", "-c", "echo 'ruok' | nc localhost 2181 | grep imok"]
      interval: 10s
      timeout: 5s
      retries: 5

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    restart: unless-stopped
    depends_on:
      zookeeper:
        condition: service_healthy
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9093,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_LOG_RETENTION_HOURS: 168  # 7 days
      KAFKA_LOG_SEGMENT_BYTES: 1073741824  # 1GB
      KAFKA_LOG_CLEANUP_POLICY: "delete"
    volumes:
      - kafka_data:/var/lib/kafka/data
    networks:
      - auren-network
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9093"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    # Remove in production
    # ports:
    #   - "127.0.0.1:9092:9092"

  # Wait for dependencies script
  wait-for-deps:
    image: busybox:latest
    depends_on:
      timescaledb:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy
    command: echo "All dependencies are ready!"
    networks:
      - auren-network

  # Biometric Bridge API
  biometric-api:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    depends_on:
      wait-for-deps:
        condition: service_completed_successfully
    environment:
      RUN_MODE: api
      POSTGRES_URL: postgresql://auren:${POSTGRES_PASSWORD:-secure_password}@timescaledb:5432/auren_biometric
      REDIS_URL: redis://redis:6379
      KAFKA_BOOTSTRAP_SERVERS: kafka:9093
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      API_PORT: 8000
      LOG_LEVEL: ${LOG_LEVEL:-info}
    ports:
      - "${API_PORT:-8000}:8000"
    networks:
      - auren-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

  # Biometric Bridge Consumer
  biometric-consumer:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    depends_on:
      wait-for-deps:
        condition: service_completed_successfully
    environment:
      RUN_MODE: consumer
      POSTGRES_URL: postgresql://auren:${POSTGRES_PASSWORD:-secure_password}@timescaledb:5432/auren_biometric
      REDIS_URL: redis://redis:6379
      KAFKA_BOOTSTRAP_SERVERS: kafka:9093
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      LOG_LEVEL: ${LOG_LEVEL:-info}
    networks:
      - auren-network
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: ${CONSUMER_REPLICAS:-3}
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M

  # Kafka UI for monitoring (dev only)
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    restart: unless-stopped
    depends_on:
      - kafka
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9093
      KAFKA_CLUSTERS_0_ZOOKEEPER: zookeeper:2181
      DYNAMIC_CONFIG_ENABLED: "true"
    ports:
      - "${KAFKA_UI_PORT:-8081}:8080"
    networks:
      - auren-network
    profiles:
      - dev

networks:
  auren-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  timescale_data:
    driver: local
  redis_data:
    driver: local
  kafka_data:
    driver: local
  zookeeper_data:
    driver: local
  zookeeper_logs:
    driver: local
"""

# =============================================================================
# KUBERNETES MANIFESTS
# =============================================================================

K8S_DEPLOYMENT_YAML = """
apiVersion: v1
kind: Namespace
metadata:
  name: auren
---
apiVersion: v1
kind: Secret
metadata:
  name: auren-secrets
  namespace: auren
type: Opaque
stringData:
  postgres-password: "your-secure-password"
  openai-api-key: "your-openai-key"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: biometric-bridge-api
  namespace: auren
spec:
  replicas: 3
  selector:
    matchLabels:
      app: biometric-bridge-api
  template:
    metadata:
      labels:
        app: biometric-bridge-api
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: api
        image: auren-biometric-bridge:latest
        imagePullPolicy: Always
        env:
        - name: RUN_MODE
          value: "api"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: auren-secrets
              key: postgres-password
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: auren-secrets
              key: openai-api-key
        - name: POSTGRES_URL
          value: "postgresql://auren:$(POSTGRES_PASSWORD)@timescaledb:5432/auren_biometric"
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka:9093"
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /readiness
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: biometric-bridge-api
  namespace: auren
spec:
  selector:
    app: biometric-bridge-api
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
"""

# =============================================================================
# DEPLOYMENT GUIDE
# =============================================================================

DEPLOYMENT_GUIDE = """
# AUREN BIOMETRIC BRIDGE - PRODUCTION DEPLOYMENT GUIDE

## Prerequisites
- Docker 20.10+ & Docker Compose v2
- Python 3.11+ (for local development)
- 8GB RAM minimum
- 50GB disk space

## Environment Setup

1. Create `.env` file:
```bash
cat > .env << EOF
# Database
POSTGRES_PASSWORD=your-secure-password-here

# Redis
REDIS_PASSWORD=your-redis-password

# Kafka
KAFKA_HEAP_OPTS=-Xmx1G -Xms1G

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

# API Configuration
API_PORT=8000
CONSUMER_REPLICAS=3

# Monitoring (optional)
KAFKA_UI_PORT=8081

# Logging
LOG_LEVEL=info
EOF
```

2. Create required directories:
```bash
mkdir -p sql/init logs
```

## Local Development

```bash
# Install dependencies
python -m venv venv
source venv/bin/activate  # or `venv\\Scripts\\activate` on Windows
pip install -r requirements.txt

# Start infrastructure only
docker-compose up -d timescaledb redis kafka zookeeper

# Run database migrations
export POSTGRES_URL=postgresql://auren:secure_password@localhost:5432/auren_biometric
python -m alembic upgrade head

# Start API locally
python main.py
```

## Production Deployment

### Docker Compose Deployment

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Scale consumers
docker-compose up -d --scale biometric-consumer=5

# View logs
docker-compose logs -f biometric-api
docker-compose logs -f biometric-consumer

# Monitor health
curl http://localhost:8000/health
```

### Kubernetes Deployment

```bash
# Build and push image
docker build -t auren-biometric-bridge:latest .
docker tag auren-biometric-bridge:latest your-registry/auren-biometric-bridge:latest
docker push your-registry/auren-biometric-bridge:latest

# Deploy to Kubernetes
kubectl apply -f k8s/

# Check status
kubectl get pods -n auren
kubectl logs -n auren -l app=biometric-bridge-api

# Scale deployment
kubectl scale deployment biometric-bridge-api -n auren --replicas=5
```

## Security Hardening

1. **Network Isolation**:
   - Use internal networks only
   - Enable firewall rules
   - Use VPN for management

2. **Secrets Management**:
   ```bash
   # Use Docker secrets
   echo "your-password" | docker secret create postgres_password -
   
   # Or use external secret manager
   export POSTGRES_PASSWORD=$(vault kv get -field=password secret/auren/postgres)
   ```

3. **TLS Configuration**:
   - Add nginx/traefik reverse proxy
   - Enable Kafka SSL/SASL
   - Use Redis TLS

## Monitoring & Observability

### Prometheus Metrics
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'auren-api'
    static_configs:
      - targets: ['biometric-api:8000']
```

### Grafana Dashboards
Import dashboards from `monitoring/dashboards/`

### Log Aggregation
```bash
# Using Loki
docker-compose -f docker-compose.monitoring.yml up -d
```

## Performance Tuning

### PostgreSQL/TimescaleDB
```sql
-- Optimize for time-series
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
SELECT pg_reload_conf();
```

### Redis
```bash
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Kafka
```properties
# server.properties
num.network.threads=8
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600
```

## Troubleshooting

### Health Check Failures
```bash
# Check individual components
docker-compose exec biometric-api curl http://localhost:8000/health
docker-compose exec timescaledb pg_isready
docker-compose exec redis redis-cli ping
docker-compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9093
```

### Memory Issues
```bash
# Increase Docker memory
# Docker Desktop: Preferences > Resources > Memory: 8GB

# Or use swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Connection Issues
```bash
# Test connectivity
docker-compose exec biometric-api python -c "
import asyncio
import asyncpg
async def test():
    conn = await asyncpg.connect('postgresql://auren:password@timescaledb:5432/auren_biometric')
    print(await conn.fetchval('SELECT 1'))
    await conn.close()
asyncio.run(test())
"
```

## Backup & Recovery

### Automated Backups
```bash
# Add to crontab
0 3 * * * docker-compose exec -T timescaledb pg_dump -U auren auren_biometric | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Manual Backup
```bash
# Backup
docker-compose exec timescaledb pg_dump -U auren auren_biometric > backup.sql

# Restore
docker-compose exec -T timescaledb psql -U auren auren_biometric < backup.sql
```

## First Biometric Event

```bash
# Send test webhook
curl -X POST http://localhost:8000/webhooks/oura \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "event_type": "readiness.updated",
    "user_id": "test_user_001",
    "data": {
      "readiness_score": 85,
      "hrv_balance": 75,
      "temperature_deviation": -0.3
    }
  }'

# Check cognitive state
curl http://localhost:8000/api/cognitive/state/test_user_001 \
  -H "X-API-Key: your-api-key"
```

## Production Checklist

- [ ] Environment variables configured
- [ ] Secrets stored securely
- [ ] Database migrations completed
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] TLS certificates installed
- [ ] Firewall rules configured
- [ ] Resource limits set
- [ ] Logging aggregation ready
- [ ] Incident response plan documented
- [ ] Load testing completed

## Support

- Documentation: /docs
- Metrics: /metrics
- Health: /health
- API Docs: /docs (FastAPI automatic)

CONGRATULATIONS! 🎉 
You've deployed the world's first biometric-aware AI system!
"""

# =============================================================================
# REQUIREMENTS FILE
# =============================================================================

REQUIREMENTS_TXT = """
# Core Dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0

# Async Libraries
asyncpg==0.29.0
redis[hiredis]==5.0.1
aiokafka==0.10.0

# AI/ML
langchain==0.1.0
langchain-openai==0.0.5
langgraph==0.0.26

# Security & Monitoring
tenacity==8.2.3
prometheus-client==0.19.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Utilities
pydantic==2.5.0
pydantic-settings==2.1.0
structlog==23.2.0

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
black==23.11.0
mypy==1.7.1

# Performance
uvloop==0.19.0
orjson==3.9.10
"""

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())

# =============================================================================
# END OF SECTION 12: PRODUCTION RUNTIME & DEPLOYMENT
# =============================================================================