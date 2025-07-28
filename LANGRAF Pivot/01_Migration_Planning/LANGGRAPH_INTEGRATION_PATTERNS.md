# LANGGRAPH INTEGRATION PATTERNS

## Overview

This document captures successful patterns discovered during the biometric bridge implementation and establishes best practices for the AUREN LangGraph migration.

---

## 🎯 Proven Patterns from Biometric Bridge

### 1. **Type-Safe State Management Pattern**

```python
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage, add_messages

class NEUROSState(TypedDict):
    """Complete state definition with all fields typed"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_mode: CognitiveMode
    previous_mode: Optional[CognitiveMode]
    mode_confidence: float
    latest_biometric_event: Optional[Dict[str, Any]]
    # ... 20+ more fields

# Pattern Benefits:
# ✅ IDE autocomplete
# ✅ Type checking
# ✅ Clear documentation
# ✅ Prevents runtime errors
```

### 2. **Dual Checkpoint Pattern**

```python
async def make_checkpoint_saver() -> List:
    """PostgreSQL primary + Redis fallback for <1ms latency"""
    pg_pool = await asyncpg.create_pool(
        settings.CHECKPOINT_POSTGRES_URL,
        min_size=2, max_size=10, timeout=60
    )
    pg_saver = PostgresSaver(pool=pg_pool)
    redis_saver = RedisSaver.from_url(settings.REDIS_URL)
    return [pg_saver, redis_saver]

# Pattern Benefits:
# ✅ Durability (PostgreSQL)
# ✅ Speed (Redis)
# ✅ Automatic fallback
# ✅ No single point of failure
```

### 3. **Event-Driven State Updates**

```python
class BiometricBridge:
    async def handle(self, kafka_msg):
        # 1. Parse event
        event = BiometricEvent.from_dict(json.loads(msg.value))
        
        # 2. Determine mode based on biometrics
        if event.hrv_drop > 25:
            new_mode = CognitiveMode.REFLEX
        else:
            new_mode = CognitiveMode.PATTERN
        
        # 3. Update state via Command
        await self.graph.ainvoke(
            Command("mode_switch", update={
                "current_mode": new_mode,
                "previous_mode": state.current_mode,
                "trigger": "biometric",
                "confidence": 0.95
            })
        )

# Pattern Benefits:
# ✅ Clear trigger → action flow
# ✅ Audit trail built-in
# ✅ Easy to test
# ✅ Decoupled from Kafka
```

### 4. **Graceful Degradation Pattern**

```python
async def start(self):
    try:
        # Try WebSocket connection
        async with session.ws_connect(self.ws_url) as ws:
            self.ws = ws
            await self.process_events()
    except Exception as e:
        logger.error(f"WebSocket failed: {e}")
        # Continue without WebSocket
        await self.process_events()

# Pattern Benefits:
# ✅ Service stays up
# ✅ Progressive enhancement
# ✅ Clear error handling
# ✅ No cascading failures
```

---

## 🏗️ State Management Best Practices

### 1. **Comprehensive State Schema**

```python
# DO: Define complete state upfront
class AgentState(TypedDict):
    # Identity
    agent_id: str
    user_id: str
    session_id: str
    
    # Conversation
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Memory tiers
    hot_memory: Dict[str, Any]      # Redis
    warm_memory: List[Dict]         # PostgreSQL
    cold_memory_ids: List[str]      # ChromaDB references
    
    # Operational
    error_count: int
    last_error: Optional[str]
    processing_lock: bool

# DON'T: Add fields ad-hoc
state["new_field"] = value  # ❌ Breaks type safety
```

### 2. **State Update Patterns**

```python
# DO: Use Command for complex updates
Command(
    goto="next_node",
    update={
        "multiple": "fields",
        "at": "once",
        "with": "validation"
    }
)

# DO: Return partial updates from nodes
def process_node(state: State) -> Dict:
    # Only return what changed
    return {"result": processed_value}

# DON'T: Mutate state directly
state.messages.append(msg)  # ❌ State is immutable
```

### 3. **State Versioning**

```python
class VersionedState(TypedDict):
    version: int  # Track schema version
    data: Dict[str, Any]
    
    @staticmethod
    def migrate(old_state: Dict) -> VersionedState:
        """Migrate old state to new schema"""
        if old_state.get("version", 1) < 2:
            # Apply migration
            old_state["new_field"] = "default"
        return VersionedState(version=2, data=old_state)
```

---

## 🔄 Checkpoint Strategies

### 1. **Selective Checkpointing**

```python
# DO: Checkpoint at meaningful boundaries
graph.add_node("analyze", checkpoint=True)      # ✅ Before expensive operation
graph.add_node("format", checkpoint=False)     # ✅ Skip for simple formatting

# DON'T: Checkpoint everything
graph.add_node("add_one", checkpoint=True)     # ❌ Too granular
```

### 2. **Checkpoint Metadata**

```python
# DO: Add searchable metadata
checkpoint_metadata = {
    "user_id": state["user_id"],
    "timestamp": datetime.now().isoformat(),
    "trigger": "biometric_alert",
    "mode": state["current_mode"]
}

# Enables queries like:
# "Find all checkpoints for user X in reflex mode"
```

### 3. **Checkpoint Retention**

```python
class CheckpointCleaner:
    async def cleanup_old_checkpoints(self):
        """Remove checkpoints older than retention period"""
        cutoff = datetime.now() - timedelta(days=7)
        await self.pg_pool.execute("""
            DELETE FROM checkpoints 
            WHERE created_at < $1
            AND thread_id NOT IN (
                SELECT DISTINCT thread_id 
                FROM active_sessions
            )
        """, cutoff)
```

---

## 🌊 Streaming & Real-time Patterns

### 1. **Multi-Channel Streaming**

```python
async def stream_to_clients(self, event: Dict):
    """Stream to multiple channels simultaneously"""
    tasks = []
    
    # WebSocket streaming
    if self.ws and not self.ws.closed:
        tasks.append(self.ws.send_str(json.dumps(event)))
    
    # Kafka streaming
    tasks.append(
        self.producer.send_and_wait("events", event)
    )
    
    # Redis pub/sub
    tasks.append(
        self.redis.publish("events", json.dumps(event))
    )
    
    await asyncio.gather(*tasks, return_exceptions=True)
```

### 2. **Backpressure Handling**

```python
class RateLimitedProcessor:
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_event(self, event):
        async with self.semaphore:
            # Process with concurrency limit
            return await self.graph.ainvoke(event)
```

---

## 🔌 Integration Patterns

### 1. **Service Integration Pattern**

```python
class ServiceIntegration:
    """Template for integrating external services"""
    
    def __init__(self):
        self.client = None
        self.circuit_breaker = CircuitBreaker()
    
    async def connect(self):
        """Lazy connection with retry"""
        for attempt in range(3):
            try:
                self.client = await create_client()
                break
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    async def call(self, *args, **kwargs):
        """Call with circuit breaker"""
        return await self.circuit_breaker.call(
            self._actual_call, *args, **kwargs
        )
```

### 2. **Multi-Model Integration**

```python
class ModelRouter:
    """Route to different models based on context"""
    
    def __init__(self):
        self.models = {
            "fast": ChatOpenAI(model="gpt-3.5-turbo"),
            "smart": ChatOpenAI(model="gpt-4"),
            "local": Ollama(model="llama2")
        }
    
    async def route(self, state: State) -> str:
        if state["urgency"] == "high":
            return "fast"
        elif state["complexity"] == "high":
            return "smart"
        else:
            return "local"
```

---

## 🧪 Testing Patterns

### 1. **State-Based Testing**

```python
async def test_mode_switching():
    """Test biometric trigger causes mode switch"""
    # Arrange
    initial_state = {
        "current_mode": CognitiveMode.PATTERN,
        "hrv_baseline": 65
    }
    
    # Act
    event = {"hrv": 35, "hrv_drop": 30}
    result = await graph.ainvoke(event, initial_state)
    
    # Assert
    assert result["current_mode"] == CognitiveMode.REFLEX
    assert result["previous_mode"] == CognitiveMode.PATTERN
```

### 2. **Checkpoint Testing**

```python
async def test_checkpoint_recovery():
    """Test graph recovers from checkpoint"""
    # Create checkpoint
    thread_id = "test_thread"
    checkpoint = await graph.acheckpoint(state, thread_id)
    
    # Simulate crash
    graph = None
    
    # Recover
    new_graph = create_graph()
    recovered_state = await new_graph.arestore(thread_id)
    
    assert recovered_state == state
```

---

## 🎯 Production Patterns

### 1. **Monitoring & Observability**

```python
from prometheus_client import Counter, Histogram

# Metrics
mode_switches = Counter(
    'langgraph_mode_switches_total',
    'Total mode switches',
    ['from_mode', 'to_mode', 'trigger']
)

processing_time = Histogram(
    'langgraph_processing_seconds',
    'Time to process events'
)

# Usage
with processing_time.time():
    result = await graph.ainvoke(event)
    
mode_switches.labels(
    from_mode=old_mode,
    to_mode=new_mode,
    trigger='biometric'
).inc()
```

### 2. **Error Recovery**

```python
class ResilientGraph:
    async def invoke_with_recovery(self, event):
        """Invoke with automatic recovery"""
        try:
            return await self.graph.ainvoke(event)
        except StateError as e:
            # Try to recover state
            logger.warning(f"State error: {e}")
            clean_state = self.create_clean_state()
            return await self.graph.ainvoke(event, clean_state)
        except Exception as e:
            # Log and return safe default
            logger.error(f"Unrecoverable error: {e}")
            return self.safe_default_response()
```

---

## 🚀 Migration Patterns

### 1. **Incremental Migration**

```python
class HybridAgent:
    """Run CrewAI and LangGraph in parallel during migration"""
    
    async def execute(self, task):
        # Run both systems
        crewai_result = await self.crewai_agent.execute(task)
        langgraph_result = await self.langgraph_node({"task": task})
        
        # Compare results
        if self.results_match(crewai_result, langgraph_result):
            self.confidence += 0.1
        else:
            logger.warning("Result mismatch")
            
        # Use CrewAI result until confidence high
        if self.confidence < 0.9:
            return crewai_result
        else:
            return langgraph_result
```

### 2. **State Migration**

```python
class StateMigrator:
    """Migrate CrewAI state to LangGraph format"""
    
    def migrate_agent_memory(self, crewai_memory) -> Dict:
        return {
            "messages": self.convert_messages(crewai_memory.chat_history),
            "context": crewai_memory.context_variables,
            "tools_used": [t.name for t in crewai_memory.tools],
            "timestamp": datetime.now().isoformat()
        }
```

---

## 📝 Key Takeaways

### DO's:
1. ✅ Define complete state schemas upfront
2. ✅ Use type hints everywhere
3. ✅ Implement graceful degradation
4. ✅ Add comprehensive monitoring
5. ✅ Test state transitions thoroughly

### DON'T's:
1. ❌ Mutate state directly
2. ❌ Skip error handling
3. ❌ Checkpoint too frequently
4. ❌ Ignore backpressure
5. ❌ Mix sync and async carelessly

### Remember:
- **State is immutable** - Always return new state
- **Checkpoints are powerful** - Use them wisely
- **Types are documentation** - Be explicit
- **Errors will happen** - Plan for them
- **Migration is iterative** - Don't rush

---

*Last Updated: January 20, 2025*  
*Based on: Biometric Bridge Implementation*  
*Next Update: After Memory System Migration* 