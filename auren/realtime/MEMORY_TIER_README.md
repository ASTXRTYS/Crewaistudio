# Memory Tier Tracking Implementation

## Overview
The Memory Tier Tracking system monitors and optimizes memory access patterns across AUREN's three-tier memory architecture: Redis (L1), PostgreSQL (L2), and ChromaDB (L3). It provides real-time visibility into cache effectiveness, latency metrics, and cost analysis.

## Key Features

### 1. **Tier Access Tracking**
- Tracks every memory access across all three tiers
- Records hit/miss rates for each tier
- Measures latency for each tier access
- Automatic fallthrough from Redis → PostgreSQL → ChromaDB

### 2. **Performance Metrics**
- **Latency Tracking**: Precise measurement of access times
  - Redis: ~5ms average
  - PostgreSQL: ~25ms average
  - ChromaDB: ~150ms average
- **Hit Rate Analysis**: Percentage of requests served by each tier
- **Cache Effectiveness**: Overall percentage served from Redis cache

### 3. **Cost Analysis**
- Tracks access costs per tier
- Projects daily costs based on usage patterns
- Provides cost breakdown by tier

### 4. **Optimization Intelligence**
- Identifies frequently accessed slow queries
- Suggests pre-caching opportunities
- Calculates potential latency savings

## Implementation Files

### Core Components:
1. **`memory_tier_tracking.py`** (680 lines)
   - `MemoryTierTracker`: Main tracking class
   - `TieredMemoryBackend`: Enhanced backend wrapper
   - Cost analysis and optimization logic

2. **`test_memory_tier_tracking.py`** (450 lines)
   - Comprehensive test suite
   - 15 test cases covering all scenarios
   - Integration tests with event emission

3. **`memory_tier_integration.py`** (220 lines)
   - Integration with Module D agents
   - Enhanced memory storage classes
   - Setup and configuration helpers

4. **`memory_tier_dashboard.html`** (Enhanced)
   - New Memory Tiers view with charts
   - Real-time metrics visualization
   - Optimization suggestions display

## Usage Example

```python
# Initialize memory tier tracking
tier_tracker = MemoryTierTracker(
    event_streamer=redis_streamer,
    metrics_window_size=1000,
    stats_update_interval=60
)

# Track a memory access
result, metrics = await tier_tracker.track_memory_access(
    query="What is my average HRV?",
    user_id="user123",
    agent_id="neuroscientist"
)

# Metrics include:
# - tier_accessed: 'redis' | 'postgresql' | 'chromadb'
# - total_latency_ms: Total access time
# - access_chain: Details for each tier tried
# - cache_effectiveness: Current cache hit rate
# - optimization_suggestions: Pre-caching recommendations
```

## Dashboard Integration

The Memory Tier widget shows:
1. **Tier Hit Rates** (Pie Chart)
   - Visual breakdown of which tier serves requests
   
2. **Latency Comparison** (Bar Chart)
   - Side-by-side latency comparison

3. **Cache Effectiveness** (Large Gauge)
   - Overall percentage served from Redis

4. **Tier Statistics** (Cards)
   - Hit rate and average latency per tier

5. **Optimization Suggestions** (List)
   - Actionable recommendations for improving performance

## Event Structure

The `MEMORY_TIER_ACCESS` event includes:
```json
{
  "event_type": "memory_tier_access",
  "payload": {
    "tier_accessed": "postgresql",
    "tier_latencies": {
      "redis": { "latency_ms": 5.2, "hit": false },
      "postgresql": { "latency_ms": 27.3, "hit": true }
    },
    "total_latency_ms": 32.5,
    "cache_hit": false,
    "query_type": "historical",
    "result_count": 5
  }
}
```

## Integration with Module D

To enhance agents with tier tracking:
```python
# Enhance existing agent
enhance_agent_with_tier_tracking(agent_wrapper, tier_tracker)

# Or create tiered memory storage
tiered_storage = TieredAURENMemoryStorage(
    memory_backend=backend,
    tier_tracker=tier_tracker
)
```

## Testing

Run comprehensive tests:
```bash
pytest auren/tests/test_memory_tier_tracking.py -v
```

Run integration demo:
```bash
python auren/realtime/memory_tier_integration.py
```

## Configuration

### Tier Costs (Configurable)
- Redis: $0.0001 per access
- PostgreSQL: $0.001 per access  
- ChromaDB: $0.01 per access

### Performance Targets
- Cache effectiveness: >70%
- Average latency: <50ms
- Redis hit rate: >40%

## Optimization Strategies

1. **Pre-cache Frequent Queries**
   - System identifies patterns accessed >10 times
   - Suggests Redis caching for high-latency queries

2. **Query Pattern Analysis**
   - Groups similar queries
   - Tracks access frequency and latency

3. **Cost Optimization**
   - Balances performance vs cost
   - Suggests tier adjustments based on usage

## Success Metrics

✅ **Implemented:**
- Redis → PostgreSQL → ChromaDB fallthrough tracking
- Accurate latency measurement per tier
- MEMORY_TIER_ACCESS event emission
- Dashboard widget with charts
- Cache effectiveness calculation
- Cost analysis and projections
- Optimization suggestions

✅ **Dashboard Features:**
- Real-time tier hit rate visualization
- Latency comparison charts
- Cache effectiveness gauge
- Per-tier statistics
- Optimization recommendations

## Next Steps

With Memory Tier Tracking complete, the system now provides:
- Full visibility into memory access patterns
- Actionable optimization recommendations
- Cost tracking and projections
- Real-time performance metrics

This enables data-driven decisions about:
- What to cache in Redis
- When to pre-load data
- How to optimize query patterns
- Cost vs performance tradeoffs 