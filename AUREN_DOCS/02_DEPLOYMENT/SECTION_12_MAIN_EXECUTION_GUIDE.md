# SECTION 12: MAIN EXECUTION & PRODUCTION RUNTIME GUIDE
## LangGraph Implementation - The Missing 7%

*Created: January 29, 2025*  
*Version: 1.0*  
*Purpose: Document the final production runtime layer that brings AUREN to 100%*

---

## 🎯 OVERVIEW

Section 12 provides the production-hardened runtime layer that transforms AUREN from a 93% prototype into a 100% production-ready system. This implementation completely removes CrewAI dependencies and embraces LangGraph patterns for enterprise-grade reliability.

---

## 🚀 WHAT SECTION 12 ADDS

### 1. Production Runtime Excellence
- **Graceful Lifecycle Management**: Proper startup/shutdown sequences with resource cleanup
- **Connection Pooling**: Optimized PostgreSQL and Redis connection management
- **Signal Handling**: SIGTERM/SIGINT handling for Kubernetes compatibility

### 2. LangGraph State Management
```python
# Proper state with reducers for parallel operations
class BiometricEventState(TypedDict):
    analysis_results: Annotated[dict, lambda a, b: {**a, **b}]  # Merge dicts
    insights: Annotated[List[str], add]  # Merge lists
    confidence_scores: Annotated[List[float], add]  # Merge numbers
```

### 3. Device-Specific Processing
- **Oura Ring**: HRV, readiness, sleep, activity scores
- **WHOOP Strap**: Recovery, strain, sleep performance
- **Apple Health**: Heart rate, steps, active energy
- **Manual Entry**: User-provided biometric data

### 4. Production Resilience
- **Retry Logic**: Exponential backoff with Tenacity
- **Circuit Breakers**: Graceful degradation for external services
- **Health Endpoints**: Comprehensive health, metrics, and readiness probes

### 5. Enhanced Observability
- **Streaming Results**: Server-Sent Events for real-time analysis
- **Prometheus Metrics**: Production monitoring integration
- **LangSmith Ready**: Deep debugging and tracing capabilities

---

## 🏗️ ARCHITECTURE COMPARISON

### Before (Sections 1-11): 93% Complete
```
┌─────────────────┐
│   FastAPI App   │ ← Basic HTTP server
├─────────────────┤
│ Simple Handlers │ ← No retry logic
├─────────────────┤
│   Direct DB     │ ← No connection pooling
└─────────────────┘
```

### After (Section 12): 100% Complete
```
┌─────────────────────────┐
│  LangGraph Runtime      │ ← State management
├─────────────────────────┤
│  Async Lifecycle Mgmt   │ ← Graceful shutdown
├─────────────────────────┤
│  Device Routing Graph   │ ← Conditional edges
├─────────────────────────┤
│  PostgreSQL Checkpoint  │ ← Persistent memory
├─────────────────────────┤
│  Retry & Circuit Break  │ ← Resilience
└─────────────────────────┘
```

---

## 📦 DEPLOYMENT

### Prerequisites
- Docker and Docker Compose installed
- PostgreSQL, Redis running (via existing docker-compose)
- Port 8888 available (or configure as needed)

### Quick Deploy
```bash
# From remote workspace
chmod +x scripts/deploy_langgraph_remote.sh
./scripts/deploy_langgraph_remote.sh

# Transfer to server
scp /tmp/section12_langgraph.tar.gz root@144.126.215.218:/tmp/

# On server
ssh root@144.126.215.218
mkdir -p /opt/auren_deploy/section_12_langgraph
cd /opt/auren_deploy/section_12_langgraph
tar xzf /tmp/section12_langgraph.tar.gz
./deploy_on_server.sh
```

### Environment Variables
```bash
POSTGRES_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379
OPENAI_API_KEY=your-key-here
AUREN_MASTER_API_KEY=generated-during-deploy
LANGGRAPH_AES_KEY=generated-for-encryption
LANGSMITH_API_KEY=optional-for-observability
```

---

## 🧪 TESTING

### Health Check
```bash
curl http://localhost:8888/health | jq
```

Expected response:
```json
{
  "status": "healthy",
  "version": "12.0.0",
  "runtime": "langgraph",
  "components": {
    "postgres": "healthy",
    "redis": "healthy",
    "langgraph": "healthy",
    "checkpointer": "healthy"
  }
}
```

### Process Biometric Event
```bash
curl -X POST http://localhost:8888/webhooks/oura \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "event_id": "evt_123",
    "hrv_rmssd": 25,
    "readiness_score": 65,
    "sleep_score": 80
  }'
```

### Stream Analysis
```bash
curl -X POST http://localhost:8888/analyze/test_user \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: text/event-stream" \
  -d '{"request": "analyze my recovery"}'
```

---

## 🔄 MIGRATION PATH

### Phase 1: Parallel Deployment (Recommended)
1. Deploy Section 12 on port 8889
2. Test thoroughly with real traffic
3. Monitor for 24-48 hours
4. Compare metrics with existing service

### Phase 2: Cutover
```bash
# Stop old service
cd /opt/auren_deploy/biometric-bridge
docker-compose down

# Verify Section 12 is healthy
curl http://localhost:8888/health

# Update any external references if needed
```

### Rollback Plan
```bash
# If issues arise
cd /opt/auren_deploy/section_12_langgraph
docker-compose down

# Restore previous service
cd /opt/auren_deploy/biometric-bridge
docker-compose up -d
```

---

## 🎯 KEY IMPROVEMENTS

### 1. No More CrewAI
- Removed all CrewAI dependencies
- Pure LangGraph implementation
- Cleaner, more maintainable code

### 2. Production Patterns
```python
# Connection with retry
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
async def create_postgres_pool():
    # Resilient connection logic
```

### 3. State Management
```python
# Parallel processing with proper merging
class AURENSystemState(TypedDict):
    recent_events: Annotated[List[dict], add]
    hypotheses: Annotated[dict, lambda a, b: {**a, **b}]
    patterns_detected: Annotated[List[dict], add]
```

### 4. Memory Persistence
```python
# PostgreSQL checkpointing
checkpointer = PostgresSaver.from_conn_string(postgres_url)
graph = builder.compile(checkpointer=checkpointer)
```

---

## 📊 MONITORING

### Prometheus Metrics
- `auren_langgraph_ready`: Service readiness
- `postgres_pool_size`: Connection pool size
- `postgres_pool_free`: Available connections

### Logs
```bash
docker logs -f auren_section12_langgraph
```

### Performance Baseline
- Health check: < 100ms
- Webhook processing: < 500ms
- Analysis streaming: First byte < 200ms

---

## 🚨 TROUBLESHOOTING

### Common Issues

1. **PostgreSQL Connection Failed**
   - Check POSTGRES_URL format
   - Verify PostgreSQL is running
   - Check network connectivity

2. **Redis Connection Failed**
   - Verify REDIS_URL
   - Check Redis is running
   - Ensure no firewall blocking

3. **LangGraph Import Error**
   - Verify langgraph==0.0.26 installed
   - Check Python version (3.11+)

4. **Memory Issues**
   - Monitor container memory usage
   - Adjust PostgreSQL pool size
   - Check for memory leaks in long-running analysis

---

## 🎉 SUCCESS METRICS

Section 12 is successful when:
- ✅ All health checks pass
- ✅ Zero CrewAI dependencies
- ✅ Webhook processing works for all devices
- ✅ Streaming analysis delivers real-time insights
- ✅ Graceful shutdown completes cleanly
- ✅ Metrics show stable performance

---

## 📚 REFERENCES

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [AUREN State of Readiness](../../auren/AUREN_STATE_OF_READINESS_REPORT.md)
- [Section 9 Security](../../app/SECTION_9_SECURITY_README.md)
- [Biometric Deployment Guide](BIOMETRIC_SYSTEM_DEPLOYMENT_GUIDE.md)

---

*This guide documents the final evolution of AUREN to 100% production readiness.*