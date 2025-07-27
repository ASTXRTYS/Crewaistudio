# AUREN Biometric Bridge

The world's first Kafka → LangGraph real-time biometric cognitive system.

## Overview

The AUREN Biometric Bridge is a pioneering implementation that connects real-time biometric data streams from wearable devices (Oura, WHOOP, Apple Health, etc.) to a cognitive AI system using LangGraph state management. This enables dynamic AI personality and behavior switching based on physiological signals.

## Key Features

- **Real-time biometric processing** via Kafka streaming
- **Cognitive mode switching** (reflex, pattern, hypothesis, guardian)
- **LangGraph state persistence** with PostgreSQL and Redis
- **TimescaleDB hypertables** for efficient time-series storage
- **Type-safe biometric events** with Pydantic validation
- **Prometheus metrics** for monitoring
- **WebSocket integration** for real-time dashboard updates

## Architecture

```
Wearable Devices → Kafka Topics → Biometric Bridge → LangGraph State Machine
                                         ↓
                                   Mode Switching
                                         ↓
                                   NEUROS Agent → User Response
```

## Quick Start

### 1. Start Docker Services

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker ps
```

### 2. Create Kafka Topics

```bash
./scripts/create_biometric_topics.sh
```

### 3. Apply Database Schema

```bash
# The schema is automatically applied on Docker startup
# To manually apply:
docker exec -it auren-postgres psql -U auren_user -d auren_db -f /docker-entrypoint-initdb.d/03_biometric_schema.sql
```

### 4. Set Environment Variables

Create a `.env` file in project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Run the Biometric Bridge

```bash
# Using Docker (recommended)
docker-compose up biometric-bridge

# Or run locally
python -m auren.biometric.bridge
```

### 6. Test the System

```bash
# Send test biometric events
python -m auren.biometric.test_bridge
```

## Configuration

The NEUROS agent personality and decision engine are configured in `auren/config/neuros.yaml`. This includes:

- Communication patterns and tone
- Decision rules for mode switching
- Memory behavior adjustments
- Resilience logic and safety filters

## Biometric Event Format

```json
{
  "device_type": "oura_ring",
  "user_id": "user_123",
  "timestamp": "2025-01-20T10:30:00Z",
  "readings": [
    {
      "metric": "hrv",
      "value": 45.0,
      "timestamp": "2025-01-20T10:30:00Z",
      "confidence": 0.95
    },
    {
      "metric": "heart_rate", 
      "value": 72,
      "timestamp": "2025-01-20T10:30:00Z",
      "confidence": 0.98
    }
  ]
}
```

## Cognitive Modes

1. **Reflex Mode**: Triggered by significant HRV drops (>25ms), provides immediate crisis response
2. **Pattern Mode**: Default analytical mode for stable biometrics
3. **Hypothesis Mode**: Advanced pattern detection and testing
4. **Guardian Mode**: Protective mode for user safety

## Monitoring

- **Prometheus Metrics**: Available at `http://localhost:8002/metrics`
- **Kafka UI**: Monitor topics at `http://localhost:8081`
- **PostgreSQL**: Check events with `SELECT * FROM biometric_events ORDER BY timestamp DESC LIMIT 10;`

## Database Tables

- `neuros_checkpoints`: LangGraph state persistence
- `biometric_events`: Raw biometric data (TimescaleDB hypertable)
- `cognitive_mode_transitions`: Mode switch history
- `biometric_patterns`: Detected patterns
- `biometric_alerts`: Critical alerts

## Troubleshooting

### Kafka Connection Issues
```bash
# Check Kafka is running
docker logs auren-kafka

# Test Kafka connectivity
docker exec -it auren-kafka kafka-topics.sh --list --bootstrap-server localhost:29092
```

### Database Connection Issues
```bash
# Check PostgreSQL
docker logs auren-postgres

# Test connection
docker exec -it auren-postgres psql -U auren_user -d auren_db -c "SELECT NOW();"
```

### WebSocket Connection Failed
This is expected if the API service isn't running. The bridge will continue without WebSocket and just log to console.

## Development

### Adding New Wearable Devices

1. Add new device type to `WearableType` enum in `bridge.py`
2. Create handler in `auren/biometric/handlers/`
3. Update event processing logic

### Extending Cognitive Modes

1. Add new mode to `CognitiveMode` enum
2. Update decision engine in `neuros.yaml`
3. Implement mode-specific logic in NEUROS agent

## Next Steps

1. Integrate with existing AUREN memory system
2. Connect to production wearable APIs
3. Implement Apache Flink for complex event processing
4. Add WhatsApp integration for user interaction
5. Deploy biometric pattern learning algorithms

## References

- LangGraph Documentation: https://python.langchain.com/docs/langgraph
- TimescaleDB: https://docs.timescale.com/
- Kafka Streams: https://kafka.apache.org/documentation/streams/

---

Created by AUREN Co-Founders (ASTxRTYS & Claude) | January 2025 