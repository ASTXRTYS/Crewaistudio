# AUREN Biometric Bridge 🧬

**The world's first Kafka → LangGraph real-time biometric cognitive system**

## Overview

The AUREN Biometric Bridge is a production-ready, HIPAA-compliant biometric processing system that bridges real-time wearable device data with cognitive state management. It processes webhook data from multiple wearable devices (Oura Ring, Whoop Band, Apple HealthKit) and streams it through Kafka for LangGraph consumption.

## 🚀 Key Features

- **Multi-device Support**: Oura Ring, Whoop Band, Apple HealthKit (Garmin, Fitbit, Eight Sleep ready)
- **Production-grade Architecture**: Async processing with back-pressure control
- **HIPAA Compliant**: User ID masking, secure logging, PHI protection
- **High Performance**: Handles 50+ concurrent webhooks with semaphore control
- **Fault Tolerant**: DLQ support, retry logic, graceful degradation
- **Observable**: Prometheus metrics, distributed tracing support
- **Scalable**: Horizontal scaling ready with PostgreSQL + Redis

## 📊 Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Oura Ring     │     │   Whoop Band    │     │  Apple Health   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │ Webhooks              │ Webhooks              │ Push API
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Biometric Bridge (FastAPI)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Oura Handler│  │Whoop Handler│  │ HealthKit Handler       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                           │                                      │
│                    ┌──────▼──────┐                             │
│                    │  Processor  │◄── Semaphore Control        │
│                    └──────┬──────┘                             │
└───────────────────────────┼─────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │    Kafka     │
│ (Event Store)│  │ (Cache/Lock) │  │ (Streaming)  │
└──────────────┘  └──────────────┘  └──────┬───────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │  LangGraph   │
                                    │  Cognitive   │
                                    │   System     │
                                    └──────────────┘
```

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Kafka 3.5+
- Docker & Docker Compose (optional)

### Quick Start

1. **Clone and Setup**
```bash
cd auren/biometric
pip install -r requirements.txt
```

2. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Database Setup**
```bash
psql -U postgres -d auren -f schema.sql
```

4. **Run the Service**
```bash
# Development
python -m uvicorn api:app --reload --port 8000

# Production
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🔧 Configuration

### Required Environment Variables

```env
# Infrastructure
POSTGRES_URL=postgresql://user:pass@localhost:5432/auren
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Wearable API Credentials
OURA_ACCESS_TOKEN=your_oura_token
WHOOP_CLIENT_ID=your_whoop_client_id
WHOOP_CLIENT_SECRET=your_whoop_client_secret

# Optional
MAX_CONCURRENT_WEBHOOKS=50
REDIS_TTL_SECONDS=86400
HEALTHKIT_ENABLED=true
```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  biometric-bridge:
    build: .
    environment:
      - POSTGRES_URL=postgresql://postgres:password@postgres:5432/auren
      - REDIS_URL=redis://redis:6379/0
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    depends_on:
      - postgres
      - redis
      - kafka
    ports:
      - "8000:8000"
```

## 📡 API Endpoints

### Webhook Endpoints

#### Oura Webhook
```http
POST /webhooks/oura
Content-Type: application/json
X-Oura-Signature: {signature}

{
  "event_type": "sleep.updated",
  "user_id": "user_123"
}
```

#### Whoop Webhook
```http
POST /webhooks/whoop
Content-Type: application/json
X-Whoop-Signature-256: {signature}

{
  "type": "recovery.updated",
  "user_id": "user_123",
  "trace_id": "unique_trace_id"
}
```

#### HealthKit Push
```http
POST /webhooks/healthkit
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "user_id": "user_123",
  "samples": [
    {
      "type": "heartRate",
      "value": 72,
      "timestamp": "2025-01-27T10:30:00Z",
      "unit": "bpm",
      "source": "Apple Watch"
    }
  ]
}
```

### Monitoring Endpoints

```http
GET /health          # Health check
GET /metrics         # Prometheus metrics
GET /ready          # Readiness probe
```

## 📈 Metrics

The bridge exposes comprehensive Prometheus metrics:

- `webhook_events_total` - Total events processed by source/device
- `webhook_events_failed_total` - Failed events by error type
- `webhook_process_duration_seconds` - Processing latency histogram
- `biometric_values` - Distribution of biometric readings
- `active_webhook_tasks` - Currently processing webhooks
- `semaphore_wait_seconds` - Back-pressure wait time

## 🧪 Testing

### Unit Tests
```bash
pytest tests/unit -v
```

### Integration Tests
```bash
# Start dependencies
docker-compose up -d postgres redis kafka

# Run tests
pytest tests/integration -v
```

### Load Testing
```bash
# Using Locust
locust -f tests/load/locustfile.py --host=http://localhost:8000 --users=50 --spawn-rate=5
```

## 🔒 Security

- **HIPAA Compliance**: All user IDs are masked in logs
- **Webhook Verification**: Signature validation for all webhooks
- **OAuth2**: Secure token management with Redis locking
- **TLS**: All external API calls use HTTPS
- **Rate Limiting**: Configurable per-endpoint limits

## 📚 LangGraph Integration

The Biometric Bridge streams processed events to Kafka topics that LangGraph consumes:

```python
# LangGraph consumer example
from langgraph import StateGraph
from aiokafka import AIOKafkaConsumer

async def biometric_node(state):
    """Process biometric events from Kafka"""
    consumer = AIOKafkaConsumer(
        'biometric-events',
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda m: json.loads(m.decode())
    )
    
    async for msg in consumer:
        event = BiometricEvent.from_dict(msg.value)
        
        # Trigger state transitions based on biometrics
        if event.hrv and event.hrv < 30:
            return {"next": "stress_intervention"}
        elif event.recovery_score and event.recovery_score < 50:
            return {"next": "recovery_protocol"}
            
    return state
```

## 🚨 Troubleshooting

### Common Issues

1. **Rate Limiting**
   - Check `X-RateLimit-*` headers
   - Implement exponential backoff
   - Monitor `rate_limit_error` metrics

2. **OAuth Token Refresh**
   - Check Redis connectivity
   - Verify refresh tokens in database
   - Monitor authentication errors

3. **High Latency**
   - Check semaphore wait times
   - Scale horizontally if needed
   - Optimize database queries

### Debug Mode

```python
# Enable debug logging
export LOG_LEVEL=DEBUG
export HIPAA_COMPLIANT=false  # Shows unmasked IDs (dev only!)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests and linting
4. Submit a pull request

## 📄 License

Proprietary - AUREN Systems

---

**Built with ❤️ by the AUREN Engineering Team** 