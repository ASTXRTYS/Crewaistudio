# AUREN Kafka Event Pipeline

## Overview
AUREN's Kafka event pipeline provides real-time processing of health biometric events with HIPAA-compliant tokenization and comprehensive event routing.

## Architecture

### Services
- **Kafka**: Event streaming platform
- **Zookeeper**: Kafka coordination
- **Redis**: Cache and session storage
- **Postgres**: TimescaleDB for time-series data
- **Kafka UI**: Web interface for monitoring

### Event Types
- **Health Biometrics**: Tokenized PHI with preserved metadata
- **Triggers**: CEP rules for anomaly detection
- **Conversations**: Multi-agent communication

## Quick Start

### 1. Start Infrastructure
```bash
cd docker
docker-compose up -d
```

### 2. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create Topics
```python
from src.infrastructure.kafka.topics import TopicManager

manager = TopicManager()
manager.create_topics()
manager.close()
```

### 4. Run Tests
```bash
python -m pytest tests/test_kafka_integration.py -v
```

## Event Schema

### Health Biometric Event
```json
{
  "event_id": "uuid",
  "user_id": "user_hash",
  "event_type": "hrv_measurement",
  "token": "TOKENIZED_PHI",
  "metadata": {
    "percentile_rank": 0.15,
    "severity_score": 0.85,
    "trend": "declining_3_days",
    "statistical_summary": {"mean": 48.3, "stddev": 5.2},
    "timestamp_iso": "2024-01-01T10:00:00Z",
    "source_device": "Apple Watch",
    "measurement_context": "morning"
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### Trigger Event
```json
{
  "trigger_id": "uuid",
  "user_id": "user_hash",
  "trigger_type": "hrv_drop",
  "severity": 0.8,
  "context_window": ["event1", "event2"],
  "recommended_agents": ["neuroscientist", "coach"],
  "message": "HRV dropped 25% below baseline",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

## Usage Examples

### Send Health Event
```python
from src.infrastructure.kafka.producer import EventProducer
from src.infrastructure.schemas.health_events import HealthBiometricEvent

producer = EventProducer()
producer.send_biometric_event(event)
producer.close()
```

### Consume Events
```python
from src.infrastructure.kafka.consumer import EventConsumer

def handle_biometric(event):
    print(f"Processing {event.event_type}")

consumer = EventConsumer(["health.biometrics"])
consumer.start(biometric_handler=handle_biometric)
```

## Monitoring

- **Kafka UI**: http://localhost:8080
- **Redis**: localhost:6379
- **Postgres**: localhost:5432

## Troubleshooting

### Kafka Won't Start
```bash
docker-compose down -v
docker-compose up -d
```

### Connection Issues
- Ensure ports 9092, 2181 are available
- Check firewall settings
- Verify Docker network

### Test Failures
- Ensure Kafka is running: `docker ps`
- Check topic creation: `python -c "from src.infrastructure.kafka.topics import TopicManager; TopicManager().list_topics()"`
