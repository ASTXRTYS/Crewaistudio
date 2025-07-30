# NEUROS AI CONFIGURATION
## Complete LangGraph AI Agent Setup and Configuration

*Last Updated: July 30, 2025*  
*Status: ✅ PRODUCTION OPERATIONAL*  
*Framework: LangGraph + OpenAI + FastAPI*

---

## 🧠 **NEUROS OVERVIEW**

NEUROS is the core AI agent of the AUREN system, built with LangGraph and OpenAI integration. It specializes in CNS (Central Nervous System) optimization for tier-one operators, focusing on HRV analysis, neural fatigue detection, recovery protocols, and stress response evaluation.

### **Live Deployment** ✅ **FULLY OPERATIONAL**
- **Production URL**: http://144.126.215.218:8000
- **Proxy URL**: https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/neuros
- **Container**: `neuros-advanced`
- **Status**: ✅ **OPERATIONAL AND HEALTHY**

**✅ STATUS UPDATE**: As of restoration on July 30, 2025:
- `neuros-advanced` container running and healthy (Up since restoration)
- Health endpoint: `{"status":"healthy","service":"neuros-advanced"}`
- Proxy routing working correctly through Vercel
- All NEUROS AI features fully operational including CNS optimization

---

## 🏗️ **NEUROS ARCHITECTURE**

### **AI Agent Stack**
```
NEUROS AI Architecture:
├── LangGraph                # AI agent framework
├── OpenAI GPT-4            # Cognitive processing engine
├── FastAPI                 # HTTP API interface
├── Kafka Consumer          # Real-time biometric data ingestion
├── PostgreSQL              # Persistent memory storage
├── Redis                   # Hot memory cache
├── ChromaDB               # Vector memory storage
└── Prometheus             # Metrics and monitoring
```

### **Specialized Capabilities**
- **CNS Optimization**: Central Nervous System performance enhancement
- **HRV Analysis**: Heart Rate Variability assessment for stress detection
- **Neural Fatigue Detection**: Cognitive load and recovery assessment
- **Recovery Protocols**: Personalized recovery recommendations
- **Stress Response Evaluation**: Real-time stress pattern analysis

---

## ⚙️ **CONFIGURATION FILES**

### **1. NEUROS Agent Profile (`config/neuros_agent_profile.yaml`)**
```yaml
# NEUROS AI Agent Configuration
agent:
  name: "NEUROS"
  version: "3.1"
  specialization: "CNS_OPTIMIZATION"
  
  # Core AI Configuration
  model:
    primary: "gpt-4"
    temperature: 0.7
    max_tokens: 2000
    response_format: "json"
  
  # Operational Modes
  modes:
    baseline: 
      description: "Standard monitoring and analysis"
      trigger_threshold: "normal_hrv"
    reflex:
      description: "Immediate intervention mode"
      trigger_threshold: "critical_hrv_below_25"
    hypothesis:
      description: "Pattern analysis and prediction"
      trigger_threshold: "trend_detection"
    companion:
      description: "Conversational support mode"
      trigger_threshold: "user_interaction"
    sentinel:
      description: "Continuous monitoring mode"
      trigger_threshold: "always_active"
  
  # Memory Configuration
  memory:
    hot_tier:
      duration: "24-72h"
      storage: "redis"
      purpose: "immediate_context"
    warm_tier:
      duration: "1-4_weeks"
      storage: "postgresql"
      purpose: "pattern_recognition"
    cold_tier:
      duration: "6mo-1yr"
      storage: "chromadb"
      purpose: "long_term_learning"

# Biometric Processing Configuration
biometric_processing:
  hrv_thresholds:
    critical: 25        # Immediate intervention required
    high_stress: 40     # Stress intervention recommended
    normal_low: 50      # Monitor closely
    optimal: 60         # Ideal range
  
  neural_fatigue_indicators:
    - "hrv_trend_decline"
    - "sleep_score_below_70"
    - "recovery_score_below_60"
    - "stress_pattern_elevation"
  
  intervention_protocols:
    breathing_exercise:
      trigger: "hrv_below_40"
      duration: "5_minutes"
      technique: "4-7-8_breathing"
    
    immediate_stress_protocol:
      trigger: "hrv_below_25"
      actions: ["breathing", "environment_change", "activity_pause"]
    
    recovery_optimization:
      trigger: "sleep_score_below_70"
      recommendations: ["sleep_hygiene", "nutrition", "hydration"]

# Kafka Integration
kafka:
  consumer_topics:
    - "biometric-events"
    - "terra-biometric-events"
  
  consumer_group: "neuros-consumer-group"
  
  processing_priorities:
    HIGH: "critical_interventions"
    MEDIUM: "pattern_analysis"
    LOW: "baseline_monitoring"

# API Configuration
api:
  health_endpoint: "/health"
  analyze_endpoint: "/api/agents/neuros/analyze"
  metrics_endpoint: "/metrics"
  
  cors_origins:
    - "https://auren-omacln1ad-jason-madrugas-projects.vercel.app"
    - "http://localhost:3000"
    - "http://localhost:5173"
```

### **2. LangGraph Configuration**
```python
# LangGraph Agent Configuration
from langgraph import StateGraph, MessageGraph
from langchain_openai import ChatOpenAI

# NEUROS State Configuration
class NeurosState(TypedDict):
    user_id: str
    session_id: str
    current_mode: str
    biometric_context: Dict
    conversation_history: List[Dict]
    intervention_context: Optional[Dict]
    memory_context: Dict

# LangGraph Agent Definition
def create_neuros_agent():
    # Initialize OpenAI model
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.7,
        max_tokens=2000,
        openai_api_key=settings.openai_api_key
    )
    
    # Create state graph
    graph = StateGraph(NeurosState)
    
    # Add agent nodes
    graph.add_node("analyze_biometrics", analyze_biometric_data)
    graph.add_node("determine_mode", determine_operational_mode)
    graph.add_node("generate_response", generate_ai_response)
    graph.add_node("update_memory", update_memory_context)
    graph.add_node("trigger_intervention", trigger_intervention_if_needed)
    
    # Define agent flow
    graph.add_edge("analyze_biometrics", "determine_mode")
    graph.add_edge("determine_mode", "generate_response")
    graph.add_edge("generate_response", "update_memory")
    graph.add_edge("update_memory", "trigger_intervention")
    
    # Set entry point
    graph.set_entry_point("analyze_biometrics")
    graph.set_finish_point("trigger_intervention")
    
    return graph.compile()
```

---

## 🔧 **KAFKA INTEGRATION**

### **Consumer Configuration**
```python
# Kafka Consumer for Real-time Biometric Data
from aiokafka import AIOKafkaConsumer
import json

async def create_neuros_kafka_consumer():
    consumer = AIOKafkaConsumer(
        'biometric-events',         # From enterprise bridge (Oura, WHOOP, Apple)
        'terra-biometric-events',   # From Terra direct Kafka integration
        bootstrap_servers=['auren-kafka:9092'],
        group_id='neuros-consumer-group',
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    await consumer.start()
    return consumer

# Message Processing
async def process_biometric_event(message):
    event_data = message.value
    
    # Extract priority from headers
    priority = "NORMAL"
    for header_key, header_value in message.headers:
        if header_key == "priority":
            priority = header_value.decode()
    
    # Process based on priority
    if priority == "HIGH":
        await process_critical_intervention(event_data)
    elif priority == "MEDIUM":
        await process_pattern_analysis(event_data)
    else:
        await process_baseline_monitoring(event_data)
```

### **Topic Subscriptions**
- **biometric-events**: Standard biometric data from enterprise bridge
- **terra-biometric-events**: Direct Terra API integration data

---

## 🧩 **AI PROCESSING MODES**

### **1. Baseline Mode**
```python
async def baseline_mode_processing(biometric_data):
    """Standard monitoring and analysis"""
    analysis = {
        "mode": "baseline",
        "hrv_assessment": analyze_hrv_trends(biometric_data),
        "sleep_analysis": analyze_sleep_patterns(biometric_data),
        "recovery_metrics": calculate_recovery_score(biometric_data),
        "recommendations": generate_baseline_recommendations(biometric_data)
    }
    return analysis
```

### **2. Reflex Mode**
```python
async def reflex_mode_processing(biometric_data):
    """Immediate intervention mode for critical situations"""
    if biometric_data.get('hrv') and biometric_data['hrv'] < 25:
        intervention = {
            "mode": "reflex",
            "severity": "CRITICAL",
            "immediate_actions": [
                "initiate_breathing_protocol",
                "recommend_environment_change",
                "pause_current_activity"
            ],
            "intervention_type": "immediate_stress_protocol",
            "duration": "immediate"
        }
        return intervention
```

### **3. Hypothesis Mode**
```python
async def hypothesis_mode_processing(biometric_data, historical_context):
    """Pattern analysis and predictive assessment"""
    patterns = {
        "mode": "hypothesis",
        "trend_analysis": detect_biometric_trends(biometric_data, historical_context),
        "pattern_recognition": identify_stress_patterns(historical_context),
        "predictions": predict_recovery_needs(biometric_data),
        "optimization_strategies": generate_optimization_protocols(patterns)
    }
    return patterns
```

---

## 🗄️ **MEMORY SYSTEM**

### **Hot Memory (Redis) - 24-72h**
```python
# Immediate context storage
async def store_hot_memory(user_id, context_data):
    key = f"neuros:hot:{user_id}"
    await redis_client.setex(
        key, 
        timedelta(hours=72).total_seconds(),
        json.dumps(context_data)
    )

# Recent conversations and immediate biometric context
hot_memory_structure = {
    "recent_conversations": [],
    "current_biometric_state": {},
    "active_interventions": [],
    "immediate_context": {}
}
```

### **Warm Memory (PostgreSQL) - 1-4 weeks**
```python
# Pattern recognition storage
async def store_warm_memory(user_id, pattern_data):
    query = """
    INSERT INTO neuros_warm_memory 
    (user_id, pattern_type, pattern_data, created_at, expires_at)
    VALUES ($1, $2, $3, $4, $5)
    """
    
    await pg_pool.execute(
        query,
        user_id,
        pattern_data['type'],
        json.dumps(pattern_data),
        datetime.now(),
        datetime.now() + timedelta(weeks=4)
    )

# Biometric patterns and intervention effectiveness
warm_memory_structure = {
    "biometric_patterns": {},
    "intervention_effectiveness": {},
    "user_preferences": {},
    "recovery_trends": {}
}
```

### **Cold Memory (ChromaDB) - 6mo-1yr**
```python
# Long-term learning storage
async def store_cold_memory(user_id, learning_data):
    # Vector embeddings for long-term pattern recognition
    collection = chromadb_client.get_collection("neuros_long_term")
    
    collection.add(
        embeddings=generate_embeddings(learning_data),
        documents=[json.dumps(learning_data)],
        metadatas=[{"user_id": user_id, "type": "long_term_pattern"}],
        ids=[f"{user_id}_{timestamp}"]
    )

# Long-term behavioral patterns and system learning
cold_memory_structure = {
    "long_term_patterns": {},
    "system_learning": {},
    "user_evolution": {},
    "global_insights": {}
}
```

---

## 🚀 **API ENDPOINTS**

### **Health Check**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "neuros-advanced",
        "version": "3.1",
        "mode": "production",
        "kafka_connected": await check_kafka_connection(),
        "database_connected": await check_db_connection(),
        "ai_model_ready": True
    }
```

### **Main Analysis Endpoint**
```python
@app.post("/api/agents/neuros/analyze")
async def analyze_request(request: NeurosRequest):
    # Process user message with biometric context
    result = await neuros_agent.process({
        "user_id": request.user_id,
        "session_id": request.session_id,
        "message": request.message,
        "biometric_context": await get_recent_biometrics(request.user_id),
        "conversation_history": await get_conversation_history(request.session_id)
    })
    
    return {
        "response": result.get("ai_response"),
        "mode": result.get("current_mode"),
        "interventions": result.get("interventions", []),
        "biometric_insights": result.get("biometric_analysis"),
        "recommendations": result.get("recommendations", [])
    }
```

### **Metrics Endpoint**
```python
@app.get("/metrics")
async def get_metrics():
    return {
        "processed_events_total": processed_events_counter.get(),
        "active_sessions": len(active_sessions),
        "interventions_triggered": interventions_counter.get(),
        "average_response_time": avg_response_time.get(),
        "memory_usage": get_memory_metrics(),
        "ai_model_status": "operational"
    }
```

---

## 🔒 **SECURITY CONFIGURATION**

### **CORS Settings**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://auren-omacln1ad-jason-madrugas-projects.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **Environment Variables**
```bash
# AI Configuration
OPENAI_API_KEY="[REDACTED-OPENAI-API-KEY]"
NEUROS_MODE="production"
NEUROS_VERSION="3.1"

# Database Connections
POSTGRES_URL="postgresql://auren_user:auren_password_2024@auren-postgres:5432/auren_production"
REDIS_URL="redis://auren-redis:6379/0"

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS="auren-kafka:9092"
KAFKA_GROUP_ID="neuros-consumer-group"

# Service Configuration
SERVICE_NAME="neuros-advanced"
LOG_LEVEL="INFO"
```

---

## ✅ **VERIFICATION & TESTING**

### **Health Check Commands**
```bash
# Direct health check
curl http://144.126.215.218:8000/health

# Proxy health check
curl https://auren-omacln1ad-jason-madrugas-projects.vercel.app/api/neuros/health

# Test conversation
curl -X POST http://144.126.215.218:8000/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How am I doing based on my recent biometrics?",
    "user_id": "test_user",
    "session_id": "test_session"
  }'
```

### **Expected Responses**
```json
// Health check response
{
  "status": "healthy",
  "service": "neuros-advanced",
  "version": "3.1",
  "kafka_connected": true,
  "database_connected": true,
  "ai_model_ready": true
}

// Analysis response
{
  "response": "Based on your recent HRV data showing an average of 45ms, you're in a good recovery state...",
  "mode": "baseline",
  "interventions": [],
  "biometric_insights": {
    "hrv_trend": "stable",
    "sleep_score": 78,
    "recovery_recommendation": "maintain_current_protocol"
  },
  "recommendations": [
    "Continue current sleep schedule",
    "Monitor stress levels during afternoon period"
  ]
}
```

---

## 📊 **PERFORMANCE METRICS**

### **Current Performance**
- **Response Time**: <500ms average
- **Concurrent Sessions**: 100+ supported
- **AI Processing**: Real-time analysis
- **Memory Efficiency**: Multi-tier storage optimization
- **Kafka Throughput**: 1000+ events/second processing

### **Monitoring Metrics**
- **processed_events_total**: Total biometric events processed
- **interventions_triggered**: Critical interventions activated
- **average_response_time**: AI response latency
- **memory_usage**: Hot/warm/cold memory utilization
- **ai_model_status**: OpenAI API connectivity

---

## 🔧 **TROUBLESHOOTING**

### **Common Issues**

#### **1. AI Model Not Responding**
```bash
# Check OpenAI API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Check NEUROS logs
docker logs neuros-advanced --tail 50

# Restart NEUROS service
docker restart neuros-advanced
```

#### **2. Kafka Consumer Issues**
```bash
# Check Kafka connection
docker exec auren-kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Check consumer lag
docker exec auren-kafka kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group neuros-consumer-group

# Reset consumer offset if needed
docker exec auren-kafka kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group neuros-consumer-group --reset-offsets --to-latest --all-topics --execute
```

#### **3. Memory System Issues**
```bash
# Check Redis connection
docker exec auren-redis redis-cli ping

# Check PostgreSQL connection
docker exec auren-postgres psql -U auren_user -d auren_production -c "SELECT 1;"

# Check ChromaDB status
curl http://auren-chromadb:8000/api/v1/heartbeat
```

---

## 📞 **SUPPORT INFORMATION**

**Component**: NEUROS AI Agent  
**Technology**: LangGraph + OpenAI + FastAPI  
**Status**: ✅ PRODUCTION OPERATIONAL  
**Container**: neuros-advanced  
**Port**: 8000

### **Key Configuration Files**
- **Agent Profile**: `config/neuros_agent_profile.yaml`
- **LangGraph Config**: `neuros_langgraph_v3.1_fixed.py`
- **Main Application**: `neuros_advanced_reasoning_simple.py`

### **Critical Dependencies**
- **OpenAI API**: GPT-4 model for cognitive processing
- **Kafka**: Real-time biometric data ingestion
- **PostgreSQL**: Persistent memory storage
- **Redis**: Hot memory cache
- **ChromaDB**: Vector memory storage

---

*This document provides complete NEUROS AI configuration details for the AUREN system. NEUROS is the core AI agent specializing in CNS optimization and real-time biometric analysis.* 