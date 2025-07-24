# Module C: Real-Time Event Pipeline

This directory contains the complete real-time event streaming infrastructure for AUREN.

## Architecture

```
Agents → CrewAI Instrumentation → Redis Streams → WebSocket Server → Dashboard
```

## Core Components

1. **crewai_instrumentation.py** - Captures all agent events
   - Agent execution start/complete
   - LLM calls with token costs
   - Tool usage tracking
   - Agent collaboration events
   - Performance metrics

2. **multi_protocol_streaming.py** - Event distribution
   - Redis Streams (primary, low-latency)
   - Kafka (optional, high-throughput)
   - Hybrid mode for redundancy

3. **enhanced_websocket_streamer.py** - Real-time delivery
   - WebSocket server on port 8765
   - Agent-specific filtering
   - Performance threshold filtering
   - Rate limiting and authentication

## Quick Start

### Prerequisites
```bash
# Ensure Redis is running
docker run -d -p 6379:6379 redis:latest
```

### 1. Test the Pipeline
```bash
cd auren/realtime
python test_event_pipeline.py
```

Expected output:
```
✅ Redis streamer initialized
✅ CrewAI instrumentation initialized
✅ Sent event: agent_execution_started - test_001
✅ Sent event: llm_call - test_002
✅ Sent event: agent_collaboration - test_003
✅ Sent event: agent_execution_completed - test_004
✅ Retrieved 4 recent events
✅ WebSocket server configured
```

### 2. Start the WebSocket Server
```bash
python -m auren.realtime.enhanced_websocket_streamer
```

Server will start on `ws://localhost:8765`

### 3. Connect Dashboard
Open `auren/dashboard/memory_tier_dashboard.html` and update the WebSocket URL to connect.

## Integration with Module D Agents

To instrument your CrewAI agents:

```python
from auren.realtime.crewai_instrumentation import CrewAIEventInstrumentation
from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer

# Initialize streaming
redis_streamer = RedisStreamEventStreamer("redis://localhost:6379")
await redis_streamer.initialize()

# Initialize instrumentation
instrumentation = CrewAIEventInstrumentation(event_streamer=redis_streamer)

# Your agents will now be automatically tracked!
```

## Event Types

- `AGENT_EXECUTION_STARTED/COMPLETED` - Agent lifecycle
- `LLM_CALL` - Language model usage with costs
- `TOOL_USAGE` - Tool execution tracking
- `AGENT_COLLABORATION` - Multi-agent interactions
- `AGENT_DECISION` - Key decisions made
- `PERFORMANCE_METRIC` - Performance data

## Performance Features

- **Memory Tier Tracking**: See which tier (Redis/PostgreSQL/ChromaDB) serves each request
- **Token Cost Tracking**: Real-time cost monitoring per agent/tool
- **Collaboration Analytics**: Track agent teamwork effectiveness
- **Performance Metrics**: Latency, success rates, resource usage

## Security Features

- JWT authentication for WebSocket connections
- Rate limiting (configurable per minute)
- Event sanitization for PII protection
- Role-based filtering

## Next Steps

1. Connect existing agents to use instrumentation
2. Update dashboard to visualize real-time data
3. Add FastAPI backend for historical analytics
4. Deploy with production configuration 