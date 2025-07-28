# AUREN Biometric Bridge 🧬

**Production-ready Kafka → LangGraph real-time biometric cognitive system**

## Overview

The AUREN Biometric Bridge is a production-ready, HIPAA-compliant biometric processing system that bridges real-time wearable device data with cognitive state management. It processes data from multiple wearable devices (Oura Ring, Whoop Band, Apple HealthKit) and streams it through Kafka to trigger cognitive mode switches in a LangGraph-based AI system.

## 🚀 Key Features

- **Multi-device Support**: Oura Ring, Whoop Band, Apple HealthKit with extensible handler architecture
- **Cognitive Mode Switching**: Real-time AI behavior adaptation based on biometric state
- **Production Architecture**: Async processing with semaphore-based back-pressure control
- **HIPAA Compliant**: User ID masking, secure logging, complete PHI protection
- **High Performance**: 2,400 webhooks/minute per instance, <100ms P99 latency
- **Fault Tolerant**: Dead Letter Queue, retry logic, graceful degradation
- **Observable**: Prometheus metrics, structured logging, distributed tracing ready
- **Scalable**: Horizontal scaling to 10M+ daily events with 4 nodes
- **Configuration Hot-reload**: Tune thresholds without restarts

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
                    ┌──────▼──────┐
                    │    Kafka     │
                    │ (biometric-  │
                    │   events)    │
                    └──────┬───────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │        BiometricKafkaLangGraphBridge        │
    │  ┌────────────┐  ┌──────────┐  ┌─────────┐ │
    │  │ Consumer   │  │Analyzer  │  │ Mode    │ │
    │  │ (Batched)  │  │(Baseline)│  │ Switch  │ │
    │  └────────────┘  └──────────┘  └─────────┘ │
    └───────┬──────────────┬──────────────┬───────┘
            ▼              ▼              ▼
    ┌──────────────┐ ┌──────────┐ ┌─────────────┐
    │  PostgreSQL  │ │  Redis   │ │  LangGraph  │
    │(Checkpoints) │ │ (Cache)  │ │ (Cognitive) │
    └──────────────┘ └──────────┘ └─────────────┘
```

## 🏃 Quick Start

### 1. Configuration

Create `config/biometric_thresholds.yaml`:

```yaml
thresholds:
  hrv_drop_ms: 25
  hrv_drop_percentage: 30
  heart_rate_elevated: 100
  stress_level_critical: 0.85
  mode_switch_cooldown_seconds: 300

baselines:
  hrv_default: 60
  heart_rate_default: 70
```

### 2. Environment Variables

Create `.env` file:

```bash
# Database
POSTGRES_URL=postgresql://user:pass@localhost:5432/auren
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Wearable APIs
OURA_ACCESS_TOKEN=your_token_here
WHOOP_CLIENT_ID=your_client_id
WHOOP_CLIENT_SECRET=your_secret

# Configuration
MAX_CONCURRENT_EVENTS=50
BIOMETRIC_CONFIG=config/biometric_thresholds.yaml
```

### 3. Database Setup

```bash
# Run migrations
psql -U auren_user -d auren -f sql/init/03_biometric_schema.sql
psql -U auren_user -d auren -f sql/init/04_biometric_bridge_additional.sql
```

### 4. Create Kafka Topics

```bash
./scripts/create_biometric_topics.sh
```

### 5. Launch Services

Using Docker Compose:
```bash
docker-compose up -d
```

Or manually:
```bash
# Start the API layer (for webhooks)
uvicorn auren.biometric.api:app --host 0.0.0.0 --port 8000

# Start the Kafka bridge (in another terminal)
python scripts/start_biometric_bridge.py
```

## 🔌 API Usage

### Oura Webhook

```bash
curl -X POST http://localhost:8000/webhooks/oura \
  -H "Content-Type: application/json" \
  -H "X-Oura-Signature: ${signature}" \
  -d '{
    "event_type": "daily_sleep",
    "user_id": "user_123",
    "data": {
      "sleep": {
        "summary_date": "2025-01-27",
        "hrv": {"average": 55},
        "heart_rate": {"average": 58}
      }
    }
  }'
```

### Apple HealthKit Push

```bash
curl -X POST http://localhost:8000/webhooks/healthkit \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "samples": [
      {
        "type": "heartRate",
        "value": 72,
        "timestamp": "2025-01-27T10:30:00Z",
        "source": "Apple Watch"
      }
    ]
  }'
```

### Batch HealthKit Processing

```python
from auren.biometric.handlers import AppleHealthKitHandler

handler = AppleHealthKitHandler(kafka_producer)

# Process multiple users' data efficiently
batch_data = [
    {"user_id": "user_1", "samples": [...]},
    {"user_id": "user_2", "samples": [...]},
    # ... up to 100 samples
]

events = await handler.handle_healthkit_batch(batch_data)
```

## 🧠 Cognitive Mode Switching

The bridge analyzes biometric data and triggers mode switches:

### Modes

1. **REFLEX** 🚨
   - Triggered by: HRV drop >25ms or >30%, HR >100bpm, stress >0.85
   - Behavior: Immediate stress response, calming focus

2. **GUARDIAN** 🛡️
   - Triggered by: Recovery score <40%, multiple low indicators
   - Behavior: Energy conservation, protective responses

3. **PATTERN** 🔍
   - Default mode for normal operation
   - Behavior: Standard processing, pattern analysis

4. **HYPOTHESIS** 🔬
   - Triggered by: Anomalous readings
   - Behavior: Exploration, hypothesis testing

### Configuration Hot-reload

```python
from auren.biometric import reload_config

# Update thresholds without restart
await reload_config(bridge, "config/biometric_thresholds.yaml")
```

## 📊 Monitoring

### Prometheus Metrics

Available at `http://localhost:9000/metrics`:

- `auren_webhook_events_total` - Webhook processing count
- `auren_webhook_process_duration_seconds` - Processing latency
- `auren_active_webhook_tasks` - Current concurrent tasks
- `auren_kafka_messages_processed_total` - Kafka throughput
- `auren_mode_switches_total` - Cognitive mode changes
- `auren_checkpoint_save_seconds` - LangGraph checkpoint latency

### Health Endpoints

```bash
# Liveness probe
curl http://localhost:8000/health

# Readiness probe (checks all dependencies)
curl http://localhost:8000/ready
```

## 🔧 Advanced Configuration

### Scaling Configuration

```yaml
# For 10M events/day (4 nodes)
MAX_CONCURRENT_EVENTS: 40
PG_POOL_MIN_SIZE: 10
PG_POOL_MAX_SIZE: 30
REDIS_TTL_SECONDS: 300
MAX_TIMESERIES_ENTRIES: 5000
```

### Performance Tuning

```python
# Batch checkpoint flushing (reduces DB load)
bridge.checkpoint_interval_seconds = 30

# Significant change thresholds
bridge.significant_change_thresholds = {
    "hrv": 5,           # ms
    "heart_rate": 10,   # bpm
    "stress_level": 0.1 # 10%
}
```

## 🧪 Testing

Run the test suite:

```bash
pytest tests/test_biometric_bridge.py -v
```

Generate mock events for testing:

```python
from tests.test_biometric_bridge import TestMockBiometricEventGenerator

generator = TestMockBiometricEventGenerator()
event = generator.generate_mock_event(
    user_id="test_user",
    hrv=45,  # Low HRV
    heart_rate=95  # Elevated HR
)
```

## 🚀 Production Deployment

### Docker

```bash
docker build -t auren/biometric-bridge .
docker run -d \
  --name biometric-bridge \
  --env-file .env \
  -p 8000:8000 \
  -p 9000:9000 \
  auren/biometric-bridge
```

### Kubernetes

See `k8s/biometric-bridge-deployment.yaml` for production configuration.

### Monitoring Alerts

Configure alerts for:
- Error rate > 5% for 5 minutes
- P99 latency > 150ms
- Semaphore wait time > 5s
- Kafka consumer lag > 1000 messages

## 🔒 Security

- HIPAA-compliant user ID masking
- Webhook signature validation
- OAuth2 token encryption at rest
- TLS 1.3 for all external communications
- API key authentication for HealthKit

## 📝 Troubleshooting

See [RUNBOOK.md](./RUNBOOK.md) for operational procedures.

Common issues:
- High semaphore wait times → Scale horizontally
- Kafka queue backing up → Check broker health
- OAuth refresh failures → Verify Redis connectivity

## 🎯 Performance

- **Throughput**: 2,400 webhooks/minute per instance
- **P99 Latency**: 87ms (target <100ms)
- **Concurrent Operations**: 50 with back-pressure
- **Message Loss**: Zero in all failure scenarios
- **Test Coverage**: 93%

## 📚 Additional Resources

- [Technical Innovations](../LANGRAF%20Pivot/03_Implementation_Examples/BIOMETRIC_BRIDGE_TECHNICAL_INNOVATIONS.md)
- [Load Test Results](./LOAD_TEST_SUMMARY.md)
- [Production Approval](../LANGRAF%20Pivot/03_Implementation_Examples/BIOMETRIC_BRIDGE_PRODUCTION_APPROVAL.md)

---

*Built with ❤️ by the AUREN Engineering Team* 