# BIOMETRIC BRIDGE → LANGGRAPH QUICK REFERENCE 🔄

## Overview

This quick reference shows how to adapt patterns from the Biometric Bridge to LangGraph components.

## 1. Event Processing Pattern

### Biometric Bridge (Kafka Events)
```python
# Publishing biometric events
async def _send_to_kafka(self, event: BiometricEvent):
    payload = json.dumps(event.to_dict()).encode("utf-8")
    key = event.user_id.encode("utf-8")
    await self.kafka_queue.send("biometric-events", payload, key=key)
```

### LangGraph Adaptation (State Events)
```python
# Publishing state transition events
async def publish_state_transition(self, state: dict, next_node: str):
    event = {
        "state_id": state["id"],
        "current_node": state["current_node"],
        "next_node": next_node,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": state.get("metadata", {})
    }
    payload = json.dumps(event).encode("utf-8")
    key = state["id"].encode("utf-8")
    await self.kafka_queue.send("langgraph-transitions", payload, key=key)
```

## 2. State Management Pattern

### Biometric Bridge (Redis + PostgreSQL)
```python
# Storing latest biometric readings
async def _store_latest_biometrics(self, event: BiometricEvent):
    key_latest = f"biometrics:{event.user_id}:latest"
    await self.redis.setex(key_latest, TTL, json.dumps(event.to_dict()))
```

### LangGraph Adaptation (Checkpoint Storage)
```python
# Storing LangGraph checkpoints
async def save_checkpoint(self, state: dict, thread_id: str):
    # Redis for fast access
    key_latest = f"langgraph:{thread_id}:latest"
    await self.redis.setex(key_latest, TTL, json.dumps(state))
    
    # PostgreSQL for durability
    async with self.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO langgraph_checkpoints 
            (thread_id, state_data, created_at)
            VALUES ($1, $2, $3)
            """,
            thread_id, json.dumps(state), datetime.utcnow()
        )
```

## 3. Error Handling Pattern

### Biometric Bridge (Custom Exceptions)
```python
class BiometricProcessingError(Exception):
    error_type = "processing_error"

# Usage
except BiometricProcessingError as e:
    EVENTS_FAILED.labels(error_type=e.error_type).inc()
```

### LangGraph Adaptation (State Machine Errors)
```python
class LangGraphStateError(Exception):
    error_type = "state_error"

class InvalidTransitionError(LangGraphStateError):
    error_type = "invalid_transition"

class NodeExecutionError(LangGraphStateError):
    error_type = "node_execution"

# Usage in graph execution
try:
    next_state = await node.execute(state)
except NodeExecutionError as e:
    GRAPH_ERRORS.labels(
        node=node.name,
        error_type=e.error_type
    ).inc()
    # Fallback to error handling node
    return {"next": "error_handler", "error": str(e)}
```

## 4. Concurrency Control Pattern

### Biometric Bridge (Observable Semaphore)
```python
self._semaphore = ObservableSemaphore(max_concurrent_webhooks)

async with self._semaphore:
    return await self.process_webhook(source, data)
```

### LangGraph Adaptation (Parallel Node Execution)
```python
# Limit concurrent node executions
node_semaphore = ObservableSemaphore(max_concurrent_nodes)

async def execute_parallel_nodes(self, nodes: List[Node], state: dict):
    async def execute_with_limit(node):
        async with node_semaphore:
            return await node.execute(state)
    
    results = await asyncio.gather(
        *[execute_with_limit(node) for node in nodes],
        return_exceptions=True
    )
    return results
```

## 5. External API Pattern

### Biometric Bridge (Wearable APIs)
```python
async def _fetch_with_retry(self, url: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:  # Rate limited
                    await asyncio.sleep(retry_after)
```

### LangGraph Adaptation (LLM Calls)
```python
async def call_llm_with_retry(self, prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = await self.llm_client.generate(prompt)
            return response
        except RateLimitError as e:
            retry_after = e.retry_after
            await asyncio.sleep(retry_after)
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

## 6. Monitoring Pattern

### Biometric Bridge (Prometheus Metrics)
```python
EVENTS_PROCESSED = Counter("webhook_events_total", "Total events", ["source"])
PROCESS_LATENCY = Histogram("webhook_process_duration_seconds", "Latency")
```

### LangGraph Adaptation (Graph Metrics)
```python
# Graph-specific metrics
NODE_EXECUTIONS = Counter(
    "langgraph_node_executions_total",
    "Total node executions",
    ["graph_name", "node_name", "status"]
)

STATE_TRANSITIONS = Counter(
    "langgraph_transitions_total",
    "Total state transitions",
    ["from_node", "to_node"]
)

GRAPH_LATENCY = Histogram(
    "langgraph_execution_duration_seconds",
    "Graph execution latency",
    ["graph_name"],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60]
)

# Usage in graph execution
with GRAPH_LATENCY.labels(graph_name="biometric_processor").time():
    result = await graph.execute(initial_state)
```

## 7. Transactional Pattern

### Biometric Bridge (Multi-store Consistency)
```python
async with conn.transaction():
    await self._persist_biometric_event(conn, event)
    await self._store_latest_biometrics(event)
await self._send_to_kafka(event)
```

### LangGraph Adaptation (State Persistence)
```python
async def commit_state_transition(self, state: dict, next_node: str):
    async with self.pg_pool.acquire() as conn:
        async with conn.transaction():
            # Save checkpoint
            checkpoint_id = await self._save_checkpoint(conn, state)
            
            # Record transition
            await self._record_transition(
                conn, state["current_node"], next_node
            )
            
            # Update state
            state["current_node"] = next_node
            state["checkpoint_id"] = checkpoint_id
            
        # Publish after commit
        await self.publish_state_transition(state, next_node)
```

## 8. Health Check Pattern

### Biometric Bridge (Readiness Probe)
```python
@app.get("/ready")
async def readiness_check():
    # Check PostgreSQL
    await pg_pool.fetchval("SELECT 1")
    # Check Redis
    await redis.ping()
    # Check Kafka
    metrics = await processor.get_processing_metrics()
```

### LangGraph Adaptation (Graph Health)
```python
@app.get("/graph/health")
async def graph_health_check():
    health = {
        "checkpoints": await check_checkpoint_storage(),
        "active_graphs": await get_active_graph_count(),
        "node_health": await check_all_nodes_health(),
        "dependencies": {
            "llm": await check_llm_connection(),
            "memory": await check_memory_stores(),
            "tools": await check_external_tools()
        }
    }
    return health
```

## 9. Testing Pattern

### Biometric Bridge (Handler Testing)
```python
@pytest.mark.asyncio
async def test_oura_webhook_processing():
    processor = ConcurrentBiometricProcessor(mock_producer, mock_redis, mock_pg)
    result = await processor.process_webhook("oura", webhook_data)
    assert result == True
```

### LangGraph Adaptation (Graph Testing)
```python
@pytest.mark.asyncio
async def test_graph_execution():
    # Create test graph
    graph = StateGraph()
    graph.add_node("start", lambda s: {"next": "process"})
    graph.add_node("process", lambda s: {"result": "done"})
    
    # Execute with test state
    initial_state = {"user_id": "test_123", "data": "test"}
    result = await graph.execute(initial_state)
    
    assert result["result"] == "done"
    assert result["current_node"] == "end"
```

## 10. Configuration Pattern

### Biometric Bridge (Pydantic Settings)
```python
class Settings(BaseSettings):
    postgres_url: str = Field(..., env='POSTGRES_URL')
    max_concurrent_webhooks: int = Field(default=50)
```

### LangGraph Adaptation (Graph Config)
```python
class LangGraphSettings(BaseSettings):
    postgres_url: str = Field(..., env='POSTGRES_URL')
    max_concurrent_nodes: int = Field(default=10)
    checkpoint_ttl_seconds: int = Field(default=3600)
    enable_persistence: bool = Field(default=True)
    llm_model: str = Field(default="gpt-4")
    
    # Graph-specific settings
    max_retries_per_node: int = Field(default=3)
    node_timeout_seconds: int = Field(default=30)
    enable_streaming: bool = Field(default=True)
```

## Quick Implementation Checklist

When implementing a new LangGraph component:

1. **Setup**
   - [ ] Copy environment validation pattern
   - [ ] Implement health check endpoints
   - [ ] Set up Prometheus metrics

2. **Core Logic**
   - [ ] Adapt event processing for state transitions
   - [ ] Implement checkpoint storage pattern
   - [ ] Add error classification hierarchy

3. **External Integrations**
   - [ ] Use session management for API calls
   - [ ] Implement retry logic with backoff
   - [ ] Add OAuth pattern if needed

4. **Observability**
   - [ ] Add metrics for all operations
   - [ ] Implement request tracing
   - [ ] Set up structured logging

5. **Testing**
   - [ ] Unit tests for each component
   - [ ] Integration tests with mocks
   - [ ] Load tests for performance

## Example: Minimal LangGraph Service

```python
# Combining all patterns into a minimal LangGraph service
from langgraph import StateGraph
from .patterns import (
    ObservableSemaphore,
    LangGraphSettings,
    AsyncKafkaQueue,
    setup_metrics
)

class LangGraphService:
    def __init__(self):
        self.settings = LangGraphSettings()
        self.semaphore = ObservableSemaphore(self.settings.max_concurrent_nodes)
        self.kafka_queue = AsyncKafkaQueue(self.producer, self.pg_pool)
        setup_metrics()
    
    async def execute_graph(self, graph: StateGraph, initial_state: dict):
        async with self.semaphore:
            with GRAPH_LATENCY.labels(graph_name=graph.name).time():
                try:
                    result = await graph.execute(initial_state)
                    NODE_EXECUTIONS.labels(
                        graph_name=graph.name,
                        status="success"
                    ).inc()
                    return result
                except LangGraphStateError as e:
                    NODE_EXECUTIONS.labels(
                        graph_name=graph.name,
                        status="failed"
                    ).inc()
                    raise
```

---

This quick reference provides a direct mapping from Biometric Bridge patterns to LangGraph implementations, making it easy to maintain consistency across the AUREN ecosystem. 