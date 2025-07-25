# Module C: Real-Time Event Pipeline

This module provides real-time visibility into AUREN's multi-agent system through comprehensive event capture, streaming architecture, and WebSocket connectivity.

## Architecture

```
CrewAI Agents → Event Instrumentation → Redis Streams → WebSocket Server → Dashboard
```

## Core Components

### 1. CrewAI Instrumentation (`crewai_instrumentation.py`)
Captures all agent activities:
- Agent execution start/complete
- LLM calls with token tracking
- Tool usage
- Agent collaborations
- Agent decisions
- Memory tier access (Redis/PostgreSQL/ChromaDB)

### 2. Event Streaming (`multi_protocol_streaming.py`)
Supports multiple streaming backends:
- **Redis Streams** (default) - Low latency, high performance
- **Kafka** (optional) - For distributed deployments
- **Hybrid** - Both Redis and Kafka for redundancy

### 3. WebSocket Server (`enhanced_websocket_streamer.py`)
Real-time event distribution:
- JWT-based authentication (test tokens accepted for development)
- Event filtering by agent, performance threshold
- Connection management
- Performance metrics aggregation

## Quick Start

### 1. Prerequisites
```bash
# Ensure Redis is running
docker ps | grep redis
# Should show: auren-redis running on port 6379

# Install dependencies
pip install redis websockets psutil kafka-python
```

### 2. Start the WebSocket Server
```bash
python -m auren.realtime.enhanced_websocket_streamer
# Server starts on ws://localhost:8765
```

### 3. Test the Connection
Open `auren/dashboard/test_websocket.html` in your browser:
1. Click "Connect" - automatically sends authentication
2. You should see "Connected with ID: ..." message
3. Events will appear as they're generated

### 4. Generate Test Events (optional)
```bash
python -m auren.realtime.generate_test_events
# Generates various event types continuously
```

## Integration with Module D Agents

When creating agents in Module D, integrate event tracking:

```python
from auren.realtime.crewai_instrumentation import CrewAIEventInstrumentation
from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer

# Initialize streaming
redis_streamer = RedisStreamEventStreamer("redis://localhost:6379")
await redis_streamer.initialize()

# Initialize instrumentation
instrumentation = CrewAIEventInstrumentation(event_streamer=redis_streamer)

# Track agent execution
agent = Agent(role="neuroscientist", ...)
session_id, trace_id = await instrumentation.track_agent_start(agent)

# ... agent does work ...

await instrumentation.track_agent_complete(agent, session_id, success=True)
```

## Event Types

- `AGENT_EXECUTION_STARTED` - Agent begins task
- `AGENT_EXECUTION_COMPLETED` - Agent finishes task
- `AGENT_COLLABORATION` - Multiple agents working together
- `AGENT_DECISION` - Agent makes a decision
- `LLM_CALL` - LLM API usage with tokens/cost
- `TOOL_USAGE` - Tool execution
- `MEMORY_TIER_ACCESS` - Which memory tier served the request
- `HYPOTHESIS_FORMATION` - New hypothesis created
- `KNOWLEDGE_ACCESS` - Knowledge graph queried

## WebSocket Message Format

### Authentication (sent immediately on connect)
```json
{
    "token": "test-token-123",
    "agent_filter": ["neuroscientist", "training_coach"],
    "performance_threshold": 0.8,
    "subscriptions": ["all_events"]
}
```

### Connection Established Response
```json
{
    "type": "connection_established",
    "connection_id": "uuid",
    "server_time": "2024-01-24T10:30:00Z",
    "available_subscriptions": ["all_events", "agent_activity", ...],
    "agent_filter": ["neuroscientist"],
    "performance_threshold": 0.8
}
```

### Stream Event
```json
{
    "type": "stream_event",
    "event": {
        "event_id": "uuid",
        "event_type": "agent_execution_completed",
        "source_agent": {"id": "neuroscientist", "role": "Neuroscientist"},
        "payload": {...},
        "performance_metrics": {
            "latency_ms": 1234,
            "token_cost": 0.05,
            "success": true
        }
    }
}
```

## Performance Features

- Event buffering by category
- Real-time performance caching
- Collaboration metrics tracking
- Automatic performance summaries every 30s
- Connection health monitoring
- Rate limiting (100 events/minute default)

## Security Features

- JWT authentication (with test token support)
- User isolation
- Agent-specific filtering
- Performance threshold filtering
- Connection limits
- Message size limits (1MB)

## Troubleshooting

### WebSocket Disconnects Immediately
- The server expects authentication immediately on connect
- Ensure your client sends auth data in the `onopen` handler
- Check server logs for specific errors

### No Events Appearing
1. Check Redis is running: `redis-cli ping`
2. Verify event generator is running
3. Check WebSocket connection status
4. Look for errors in browser console

### Connection Refused
1. Ensure WebSocket server is running on port 8765
2. Check firewall settings
3. Try `ws://127.0.0.1:8765` instead of `localhost`

## Development Tools

### Test WebSocket Connection
```bash
python -m auren.realtime.test_websocket_connection
```

### Monitor Redis Events
```bash
redis-cli
> XRANGE auren:events - + COUNT 10
```

### Check Active Connections
The WebSocket server logs active connections and performance metrics.

## Next Steps

1. **Create Production Dashboard**: Build a full React/Vue dashboard
2. **Add GraphQL API**: For complex queries and aggregations  
3. **Implement Alerts**: Real-time notifications for critical events
4. **Add Grafana Integration**: For historical analysis
5. **Scale Horizontally**: Multiple WebSocket servers with Redis Pub/Sub 