# BIOMETRIC BRIDGE DEPLOYMENT GUIDE

**Version**: 1.0  
**Last Updated**: January 20, 2025  
**Author**: AUREN Biometric Team  
**System**: Kafka → LangGraph Cognitive Bridge  

---

## 🎯 Executive Summary

This guide provides complete deployment procedures for the AUREN Biometric Bridge - the world's first production Kafka → LangGraph biometric cognitive system. The bridge processes real-time biometric events from wearables (Oura, WHOOP, Apple Health) and triggers cognitive mode switching in the NEUROS AI agent.

**Key Components:**
- **Kafka Consumer**: Real-time biometric event streaming
- **LangGraph State Machine**: Cognitive mode switching (reflex/pattern/hypothesis/guardian)
- **TimescaleDB**: Time-series biometric data storage
- **Redis + PostgreSQL**: State persistence and checkpointing
- **AES-256 + TLS 1.3**: HIPAA-compliant PHI protection

---

## 🚀 Pre-Deployment Checklist

### System Requirements
- [ ] DigitalOcean Droplet (8GB RAM minimum)
- [ ] Docker & Docker Compose installed
- [ ] Domain configured (aupex.ai)
- [ ] SSL certificates ready
- [ ] OpenAI API key available

### Service Dependencies
```bash
# Required services (must be running)
- PostgreSQL (TimescaleDB)
- Redis
- Kafka + Zookeeper
- AUREN API service

# Optional services
- ChromaDB (semantic memory)
- Nginx (reverse proxy)
```

---

## 📦 Container Registry Setup

### 1. Build Biometric Bridge Image
```bash
# Navigate to project root
cd /root/auren-production

# Build the image
docker build -f Dockerfile.api -t auren-biometric-bridge:latest .

# Tag for registry
docker tag auren-biometric-bridge:latest registry.digitalocean.com/auren-biometric/biometric-bridge:latest
```

### 2. Push to DigitalOcean Registry
```bash
# Login to registry
doctl registry login

# Push image
docker push registry.digitalocean.com/auren-biometric/biometric-bridge:latest
```

---

## 🗄️ Database Migration

### 1. Enable TimescaleDB
```bash
# Update docker-compose.yml to use TimescaleDB image
sed -i 's/postgres:16-alpine/timescale\/timescaledb:latest-pg16/g' docker-compose.prod.yml

# Restart PostgreSQL
docker-compose -f docker-compose.prod.yml up -d postgres
```

### 2. Run Biometric Schema Migrations
```bash
# Copy migration files
cp sql/init/03_biometric_schema.sql /tmp/

# Execute migrations
docker exec -i auren-postgres psql -U auren_user -d auren_db < /tmp/03_biometric_schema.sql

# Verify hypertables
docker exec auren-postgres psql -U auren_user -d auren_db -c "SELECT * FROM timescaledb_information.hypertables;"
```

### 3. Setup PHI Encryption
```sql
-- Connect to database
docker exec -it auren-postgres psql -U auren_user -d auren_db

-- Create encryption extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Setup encryption keys
INSERT INTO encryption_keys (key_id, encrypted_key) 
VALUES ('biometric_key_2025', encode(gen_random_bytes(32), 'base64'));

-- Test encryption
SELECT encrypt_phi('test_biometric_data', 'biometric_key_2025');
```

---

## 🔧 Kafka Configuration

### 1. Create Biometric Topics
```bash
# Run topic creation script
./scripts/create_biometric_topics.sh

# Or manually create topics
docker exec -it auren-kafka kafka-topics.sh \
  --create \
  --topic biometric.events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

docker exec -it auren-kafka kafka-topics.sh \
  --create \
  --topic biometric.alerts \
  --bootstrap-server localhost:9092 \
  --partitions 1 \
  --replication-factor 1
```

### 2. Verify Topics
```bash
# List all topics
docker exec -it auren-kafka kafka-topics.sh \
  --list \
  --bootstrap-server localhost:9092

# Check topic configuration
docker exec -it auren-kafka kafka-topics.sh \
  --describe \
  --topic biometric.events \
  --bootstrap-server localhost:9092
```

---

## 🚀 Deploy Biometric Bridge

### 1. Update Docker Compose
```yaml
# Add to docker-compose.prod.yml
biometric-bridge:
  image: registry.digitalocean.com/auren-biometric/biometric-bridge:latest
  container_name: auren-biometric-bridge
  environment:
    - POSTGRES_URL=postgresql://auren_user:auren_password_2024@postgres:5432/auren_db
    - REDIS_URL=redis://redis:6379
    - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
    - WEBSOCKET_URL=ws://auren-api:8080/ws
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - LOG_LEVEL=INFO
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
    kafka:
      condition: service_healthy
  volumes:
    - ./auren:/app/auren
    - ./auren/config/neuros.yaml:/app/config/neuros.yaml:ro
  command: python -m auren.biometric.bridge
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
    interval: 30s
    timeout: 10s
    retries: 3
  networks:
    - auren-network
```

### 2. Start the Service
```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Start biometric bridge
docker-compose -f docker-compose.prod.yml up -d biometric-bridge

# Check logs
docker-compose -f docker-compose.prod.yml logs -f biometric-bridge
```

---

## 🔒 Security Configuration

### 1. TLS 1.3 for PHI Transit
```nginx
# Update nginx configuration
server {
    listen 443 ssl http2;
    server_name aupex.ai;
    
    # TLS 1.3 only
    ssl_protocols TLSv1.3;
    ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256';
    
    # PHI security headers
    add_header Cache-Control "no-store, no-cache, must-revalidate" always;
    add_header Pragma "no-cache" always;
    
    # Biometric API endpoint
    location /api/biometric/ {
        proxy_pass http://biometric-bridge:8002/;
        proxy_set_header X-Real-IP $remote_addr;
        
        # PHI audit logging
        access_log /var/log/nginx/biometric_access.log combined;
    }
}
```

### 2. Enable PHI Audit Logging
```sql
-- Create audit trigger for biometric data access
CREATE OR REPLACE FUNCTION log_biometric_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO phi_access_log (
        user_id, 
        accessor_id, 
        access_type, 
        table_name, 
        record_id
    ) VALUES (
        NEW.user_id,
        current_user,
        TG_OP,
        TG_TABLE_NAME,
        NEW.id
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to biometric tables
CREATE TRIGGER biometric_events_audit
AFTER INSERT OR UPDATE OR DELETE ON biometric_events
FOR EACH ROW EXECUTE FUNCTION log_biometric_access();
```

---

## 🧪 Testing & Verification

### 1. Send Test Biometric Event
```python
# test_biometric_event.py
from kafka import KafkaProducer
import json
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

test_event = {
    "user_id": "test_user_123",
    "device_id": "oura_ring_456",
    "event_type": "heart_rate",
    "timestamp": datetime.now().isoformat(),
    "metrics": {
        "hrv": 45,
        "heart_rate": 72,
        "stress_level": 0.7
    }
}

producer.send('biometric.events', test_event)
producer.flush()
print("Test event sent!")
```

### 2. Verify Processing
```bash
# Check Kafka consumer group
docker exec -it auren-kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group neuros-biometric-bridge \
  --describe

# Check LangGraph state
docker exec -it auren-postgres psql -U auren_user -d auren_db \
  -c "SELECT * FROM neuros_checkpoints ORDER BY created_at DESC LIMIT 5;"

# Check cognitive mode transitions
docker exec -it auren-postgres psql -U auren_user -d auren_db \
  -c "SELECT * FROM cognitive_mode_transitions ORDER BY transition_time DESC LIMIT 5;"
```

### 3. Monitor Metrics
```bash
# Health check
curl http://localhost:8002/health

# Prometheus metrics
curl http://localhost:8002/metrics

# Check logs for processing
docker logs -f auren-biometric-bridge --tail 100
```

---

## 📊 Production Monitoring

### 1. Setup Alerts
```yaml
# prometheus/alerts.yml
groups:
  - name: biometric_bridge
    rules:
      - alert: BiometricBridgeDown
        expr: up{job="biometric-bridge"} == 0
        for: 5m
        annotations:
          summary: "Biometric Bridge is down"
          
      - alert: KafkaLagHigh
        expr: kafka_consumer_lag > 1000
        for: 10m
        annotations:
          summary: "Kafka consumer lag is high"
          
      - alert: CognitiveModeStuck
        expr: rate(cognitive_mode_transitions[5m]) == 0
        for: 30m
        annotations:
          summary: "No cognitive mode transitions"
```

### 2. Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Biometric Bridge Monitoring",
    "panels": [
      {
        "title": "Events Processed",
        "targets": [{
          "expr": "rate(biometric_events_processed_total[5m])"
        }]
      },
      {
        "title": "Cognitive Mode Distribution",
        "targets": [{
          "expr": "cognitive_mode_current"
        }]
      },
      {
        "title": "Kafka Consumer Lag",
        "targets": [{
          "expr": "kafka_consumer_lag{topic='biometric.events'}"
        }]
      }
    ]
  }
}
```

---

## 🔄 Maintenance Procedures

### Daily Tasks
```bash
# Check service health
docker-compose -f docker-compose.prod.yml ps

# Verify data flow
docker exec -it auren-postgres psql -U auren_user -d auren_db \
  -c "SELECT COUNT(*) FROM biometric_events WHERE time > NOW() - INTERVAL '1 hour';"

# Review PHI access logs
docker exec -it auren-postgres psql -U auren_user -d auren_db \
  -c "SELECT * FROM phi_access_log WHERE access_time > NOW() - INTERVAL '24 hours';"
```

### Weekly Tasks
```bash
# Backup biometric data
pg_dump -h localhost -U auren_user -d auren_db \
  -t biometric_events \
  -t neuros_checkpoints \
  -t cognitive_mode_transitions \
  > biometric_backup_$(date +%Y%m%d).sql

# Encrypt backup
gpg --encrypt --recipient admin@aupex.ai biometric_backup_*.sql

# Verify TimescaleDB compression
docker exec -it auren-postgres psql -U auren_user -d auren_db \
  -c "SELECT * FROM timescaledb_information.compressed_chunk_stats;"
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Kafka Connection Failed
```bash
# Check Kafka is running
docker-compose -f docker-compose.prod.yml ps kafka

# Test connection
docker exec -it auren-kafka kafka-broker-api-versions.sh \
  --bootstrap-server localhost:9092

# Check network connectivity
docker exec -it auren-biometric-bridge ping kafka
```

#### 2. LangGraph State Errors
```bash
# Clear corrupted checkpoints
docker exec -it auren-postgres psql -U auren_user -d auren_db \
  -c "DELETE FROM neuros_checkpoints WHERE thread_id = 'problematic_thread';"

# Reset Redis checkpoints
docker exec -it auren-redis redis-cli FLUSHDB
```

#### 3. High Memory Usage
```bash
# Check container stats
docker stats auren-biometric-bridge

# Increase memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 512M
```

---

## 📚 Additional Resources

- **Biometric Bridge README**: `/auren/biometric/README.md`
- **NEUROS Configuration**: `/auren/config/neuros.yaml`
- **LangGraph Documentation**: [langchain.com/docs/langgraph](https://langchain.com/docs/langgraph)
- **Kafka Documentation**: [kafka.apache.org](https://kafka.apache.org)

---

*This deployment guide ensures the AUREN Biometric Bridge operates securely and reliably in production, processing real-time biometric data with HIPAA compliance.* 