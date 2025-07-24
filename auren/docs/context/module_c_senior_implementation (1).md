# Module C: Real-Time Systems & Dashboard - Complete Implementation Guide

## Executive Summary
This module creates comprehensive observability for AUREN's multi-agent intelligence system, showing real-time agent behavior, memory access patterns, token economics, and collaboration dynamics.

**Dashboard Access**: `http://localhost:3000` (React app) or `http://localhost:8080` (standalone)

## Implementation Phases

### Phase 1: Core Infrastructure (Day 1)
**Deliverable**: Working event streaming and WebSocket server

1. **Event Streaming Setup**
   ```bash
   # Redis Streams (already running from Module A)
   # Verify with: redis-cli ping
   
   # Optional Kafka setup if needed for scale
   docker-compose up -d kafka zookeeper
   ```

2. **Implement CrewAI Instrumentation**
   - Use `crewai_realtime_integration.py` from artifact
   - Integrates with Module D agents
   - Captures ALL agent events:
     - Execution start/stop with timing
     - LLM calls with token counts
     - Tool usage with costs
     - Hypothesis formation
     - Knowledge access WITH MEMORY TIER

3. **WebSocket Server**
   ```python
   # Run the enhanced WebSocket server
   python -m auren.realtime.websocket_server --port 8765
   ```

**Definition of Done Phase 1**:
- [ ] Event streaming captures all agent activities
- [ ] WebSocket server accepts connections
- [ ] Events flow from agents → Redis → WebSocket
- [ ] Basic event logging confirms data flow

### Phase 2: Enhanced Monitoring Integration (Day 1-2)
**Deliverable**: Full agent observability with memory tier tracking

1. **Memory Tier Visibility**
   ```python
   # Enhanced memory tracking to show which tier
   class TieredMemoryTracker(AURENMemoryStorage):
       async def load(self, query: str = "", limit: int = 100):
           # Track which tier serves the request
           tier_accessed = None
           latency_by_tier = {}
           
           # Try Redis first (Tier 1)
           start = time.time()
           redis_result = await self._check_redis_cache(query)
           latency_by_tier['redis'] = time.time() - start
           
           if redis_result:
               tier_accessed = 'redis_immediate'
           else:
               # Try PostgreSQL (Tier 2)
               start = time.time()
               pg_result = await self._check_postgresql(query)
               latency_by_tier['postgresql'] = time.time() - start
               
               if pg_result:
                   tier_accessed = 'postgresql_structured'
               else:
                   # Fall back to ChromaDB (Tier 3)
                   start = time.time()
                   chroma_result = await self._check_chromadb(query)
                   latency_by_tier['chromadb'] = time.time() - start
                   tier_accessed = 'chromadb_semantic'
           
           # Emit tier access event
           await self.event_instrumentation.stream_event(
               AURENStreamEvent(
                   event_type=AURENEventType.MEMORY_TIER_ACCESS,
                   payload={
                       'tier_accessed': tier_accessed,
                       'query': query,
                       'latency_by_tier': latency_by_tier,
                       'items_retrieved': len(result)
                   }
               )
           )
   ```

2. **Dynamic Agent Detection**
   ```python
   # Auto-detect active agents
   class AgentRegistry:
       def __init__(self):
           self.active_agents = {}
           self.agent_capabilities = {}
       
       def register_agent(self, agent_id, agent_instance):
           self.active_agents[agent_id] = {
               'instance': agent_instance,
               'registered_at': datetime.now(),
               'last_activity': datetime.now(),
               'capabilities': self._extract_capabilities(agent_instance)
           }
       
       def get_active_agents(self):
           # Return only agents active in last 5 minutes
           cutoff = datetime.now() - timedelta(minutes=5)
           return {
               aid: info for aid, info in self.active_agents.items()
               if info['last_activity'] > cutoff
           }
   ```

**Definition of Done Phase 2**:
- [ ] Memory tier access is tracked and visible
- [ ] Dashboard shows WHICH tier (Redis/PostgreSQL/ChromaDB) served each request
- [ ] Active agents dynamically detected
- [ ] Agent capabilities extracted and displayed

### Phase 3: Production Dashboard (Day 2-3)
**Deliverable**: Full-featured React dashboard with all visualizations

1. **React Dashboard Setup**
   ```bash
   # Create React app with TypeScript
   npx create-react-app auren-dashboard --template typescript
   cd auren-dashboard
   npm install recharts react-use-websocket @mui/material
   ```

2. **Enhanced Dashboard Features**
   ```typescript
   // Core dashboard components to implement
   
   // 1. Memory Tier Visualization
   const MemoryTierFlow = () => {
     // Shows flow: Query → Redis → PostgreSQL → ChromaDB
     // With latencies and hit rates for each tier
   }
   
   // 2. Knowledge Access Patterns
   const KnowledgeHeatmap = () => {
     // Interactive heatmap showing:
     // - Knowledge item access frequency
     // - Which agents access which knowledge
     // - Time-based patterns
   }
   
   // 3. Token Economics Dashboard
   const TokenEconomics = () => {
     // Real-time cost tracking:
     // - Cost per agent per hour
     // - Cost per user query
     // - Projected daily/monthly costs
     // - Cost optimization suggestions
   }
   
   // 4. Agent Collaboration Network
   const CollaborationGraph = () => {
     // D3.js force-directed graph showing:
     // - Active agent nodes
     // - Collaboration edges with frequency
     // - Real-time updates as agents interact
   }
   ```

3. **API Endpoints for Dashboard**
   ```python
   @app.get("/api/v2/memory/tier-stats")
   async def get_memory_tier_stats(window_hours: int = 24):
       return {
           "tier_hit_rates": {
               "redis": 0.45,      # 45% served from Redis
               "postgresql": 0.40,  # 40% from PostgreSQL  
               "chromadb": 0.15    # 15% from ChromaDB
           },
           "average_latencies_ms": {
               "redis": 5,
               "postgresql": 25,
               "chromadb": 150
           },
           "cost_by_tier": {
               "redis": 0.10,      # $0.10 for Redis operations
               "postgresql": 0.35,  # $0.35 for PostgreSQL
               "chromadb": 2.15    # $2.15 for vector searches
           }
       }
   
   @app.get("/api/v2/agents/active")
   async def get_active_agents():
       # Returns only currently active agents
       return {
           "active_count": 1,  # Just neuroscientist if that's all running
           "agents": [{
               "id": "neuroscientist",
               "status": "active",
               "last_activity": "2025-01-24T10:30:00Z",
               "current_load": 3,  # Active tasks
               "capabilities": ["hypothesis_formation", "biometric_analysis"]
           }]
       }
   ```

**Definition of Done Phase 3**:
- [ ] React dashboard running on port 3000
- [ ] All 4 core visualizations working
- [ ] Real-time updates via WebSocket
- [ ] Memory tier visibility implemented
- [ ] Dynamic agent detection working

### Phase 4: Advanced Analytics (Day 3-4)
**Deliverable**: Predictive analytics and optimization recommendations

1. **Pattern Detection**
   ```python
   class AURENAnalytics:
       def analyze_knowledge_patterns(self):
           # Identify:
           # - Most accessed knowledge by time of day
           # - Knowledge gaps (queries with no results)
           # - Collaboration patterns that work best
           
       def predict_token_usage(self):
           # Based on historical patterns:
           # - Predict next hour's token usage
           # - Alert if approaching limits
           # - Suggest optimizations
           
       def optimization_recommendations(self):
           # Automated suggestions:
           # - "Cache these 5 knowledge items in Redis"
           # - "Neuroscientist + Sleep agent collaborate 80% of time"
           # - "Consider pre-computing these embeddings"
   ```

2. **Export and Reporting**
   ```python
   @app.get("/api/v2/export/analytics")
   async def export_analytics(format: str = "csv"):
       # Export options:
       # - Token usage by agent/day
       # - Knowledge access patterns
       # - Memory tier performance
       # - Cost breakdown
   ```

**Definition of Done Phase 4**:
- [ ] Pattern detection algorithms implemented
- [ ] Predictive analytics for token usage
- [ ] Optimization recommendations generated
- [ ] Export functionality working

## Complete File Structure
```
auren/
├── realtime/
│   ├── __init__.py
│   ├── crewai_instrumentation.py      # From artifact 1
│   ├── event_streaming.py             # Redis/Kafka streaming
│   ├── websocket_server.py            # Real-time server
│   ├── analytics.py                   # Pattern detection
│   └── performance_monitor.py         # System monitoring
├── dashboard/
│   ├── backend/
│   │   ├── api.py                     # FastAPI endpoints
│   │   ├── graphql_schema.py          # GraphQL option
│   │   └── data_aggregator.py         # Analytics
│   └── frontend/
│       ├── src/
│       │   ├── components/
│       │   │   ├── MemoryTierFlow.tsx
│       │   │   ├── KnowledgeHeatmap.tsx
│       │   │   ├── TokenEconomics.tsx
│       │   │   └── CollaborationGraph.tsx
│       │   └── App.tsx
│       └── package.json
└── tests/
    └── test_realtime_integration.py

```

## Deployment Instructions

### Development Setup
```bash
# 1. Start all services
docker-compose up -d redis postgresql

# 2. Run event streaming
python -m auren.realtime.websocket_server

# 3. Start dashboard backend
python -m auren.dashboard.backend.api

# 4. Start React dashboard
cd auren/dashboard/frontend
npm install
npm start

# Dashboard available at http://localhost:3000
```

### Production Setup
```nginx
# Nginx configuration
server {
    listen 80;
    server_name auren-dashboard.local;
    
    location / {
        proxy_pass http://localhost:3000;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
    }
    
    location /ws {
        proxy_pass http://localhost:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Integration with Existing Modules

### From Module A (Data Layer)
- Uses PostgreSQL event store for historical data
- Reads from Redis for real-time metrics
- Integrates with TimescaleDB for time-series

### From Module B (Intelligence)
- Tracks hypothesis formation/validation
- Monitors knowledge graph access
- Shows learning velocity

### From Module D (Agents)
- Instruments all CrewAI agents
- Tracks collaboration patterns
- Monitors tool usage and costs

## Performance Benchmarks

Target metrics:
- Event capture latency: <10ms
- Dashboard update latency: <100ms
- WebSocket message throughput: 10,000 msgs/sec
- Memory overhead per agent: <50MB
- Dashboard load time: <2 seconds

## Testing Checklist

- [ ] Unit tests for event instrumentation
- [ ] Integration tests with Module D agents  
- [ ] WebSocket connection reliability tests
- [ ] Dashboard component tests
- [ ] End-to-end workflow tests
- [ ] Performance/load tests

## Questions for Implementation

1. **Persistence**: How long to retain events? (Recommendation: 7 days detailed, 90 days aggregated)
2. **Authentication**: JWT tokens or session-based? (Recommendation: JWT with refresh tokens)
3. **Deployment**: Kubernetes or Docker Compose? (Recommendation: Docker Compose for MVP)
4. **Monitoring**: Grafana integration needed? (Recommendation: Yes, for production)

## Success Criteria

The implementation is complete when:
1. All agent activities are captured in real-time
2. Memory tier access is fully visible
3. Token costs are tracked per agent/tool/query
4. Dashboard dynamically shows only active agents
5. Knowledge access patterns are clear and actionable
6. Export functionality provides useful analytics

## Notes for Senior Engineer

- The WebSocket streaming can handle 10K+ concurrent connections with proper tuning
- Consider using Redis Pub/Sub for horizontal scaling
- The React dashboard can be replaced with your preferred framework
- All components are designed to be stateless for easy scaling
- Performance monitoring is built-in from day one

This is a comprehensive system that will give unprecedented visibility into AUREN's intelligence. The senior engineer has full autonomy to improve any component while maintaining the core observability goals.