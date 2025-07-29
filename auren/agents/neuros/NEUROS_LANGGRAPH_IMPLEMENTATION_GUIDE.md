# NEUROS LangGraph Implementation Guide
## Sophisticated Cognitive State Machine for Elite Performance Optimization

*Created: July 29, 2025*  
*Version: 3.0.0 - Full LangGraph Integration*

---

## 🧠 Overview

This is the most sophisticated version of NEUROS, implementing a complete cognitive state machine using LangGraph. It brings the full 358-line YAML personality profile to life with:

- **6 Dynamic Operational Modes** with confidence scoring
- **Three-Tier Memory System** (L1 Real-time, L2 Working, L3 Long-term)
- **Pattern Synthesis** across biometric and conversational data
- **Hypothesis Generation** and testing frameworks
- **GPT-4 Integration** with context-aware prompting
- **State Persistence** via PostgreSQL checkpointing

---

## 🎯 Key Features

### 1. Cognitive State Machine
The LangGraph implementation models NEUROS as a sophisticated state machine with these nodes:

```
Perception → Mode Analysis → Memory Integration → Pattern Synthesis → Response Generation → Memory Update
```

Each node represents a cognitive process:
- **Perception**: Analyzes incoming messages for stress, complexity, and emotional indicators
- **Mode Analysis**: Determines optimal operational mode with confidence scoring
- **Memory Integration**: Accesses three-tier memory system
- **Pattern Synthesis**: Identifies cross-tier patterns and generates hypotheses
- **Response Generation**: Creates contextual responses using full personality
- **Memory Update**: Persists insights across memory tiers

### 2. Six Operational Modes

| Mode | Purpose | Triggers |
|------|---------|----------|
| **BASELINE** | Default analytical state | General questions, no specific triggers |
| **HYPOTHESIS** | Theory formation and testing | "Why", "how", pattern-seeking language |
| **COMPANION** | Empathetic support | Stress indicators, emotional language |
| **SYNTHESIS** | Big-picture integration | Requests for overall insights, data analysis |
| **COACH** | Action planning | Goal-setting, protocol requests |
| **PROVOCATEUR** | Growth catalyst | Self-limiting beliefs, untapped potential |

### 3. Three-Tier Memory Architecture

#### L1: Real-time Memory (Redis)
- Current conversation context
- Immediate mode and phase
- Message count and timing
- 2-hour TTL

#### L2: Working Memory (Redis)
- Recent patterns and insights
- Dominant modes over time
- Interaction frequencies
- 24-hour TTL

#### L3: Long-term Memory (PostgreSQL)
- User profile and preferences
- Historical patterns
- Breakthrough moments
- Persistent storage

### 4. Dynamic Personality System

The system builds prompts dynamically based on:
- Current cognitive state
- Active mode and confidence
- Memory context from all tiers
- Conversation phase
- Pattern strength indicators

---

## 🚀 Deployment

### Quick Deploy
```bash
# Run the deployment script
./auren/agents/neuros/deploy_langgraph_neuros.sh
```

### Manual Deployment

1. **Set Environment Variables**:
```bash
export OPENAI_API_KEY="your-api-key"
export REDIS_URL="redis://auren-redis:6379"
export DATABASE_URL="postgresql://auren_user:password@auren-postgres:5432/auren_production"
```

2. **Install Dependencies**:
```bash
pip install langgraph langchain langchain-openai redis asyncpg
```

3. **Run the Service**:
```bash
uvicorn neuros_langgraph:app --host 0.0.0.0 --port 8000
```

---

## 📡 API Endpoints

### Health Check
```bash
GET /health
```
Returns system status including OpenAI, Redis, and PostgreSQL connections.

### Process Message
```bash
POST /process
{
  "text": "Your message here",
  "session_id": "unique-session-id",
  "user_id": "user-identifier"
}
```

Response includes:
```json
{
  "response": "NEUROS response text",
  "mode": "HYPOTHESIS",
  "mode_confidence": 0.85,
  "pattern_strength": 0.72,
  "conversation_phase": "exploration",
  "hypothesis_active": "Your recovery patterns suggest...",
  "next_protocol": "Action items if in COACH mode",
  "thread_id": "session-id",
  "timestamp": "2025-07-29T10:30:00Z"
}
```

### Get Modes
```bash
GET /modes
```
Returns all available modes with descriptions.

---

## 🎮 Usage Examples

### Example 1: Stress Support (COMPANION Mode)
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I am feeling overwhelmed with work and my HRV has been dropping",
    "session_id": "stress-session-001",
    "user_id": "user123"
  }'
```

Expected: NEUROS enters COMPANION mode, acknowledges stress indicators, offers support while maintaining scientific grounding.

### Example 2: Pattern Analysis (HYPOTHESIS Mode)
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Why do I always feel tired after lunch despite good sleep?",
    "session_id": "pattern-session-002",
    "user_id": "user123"
  }'
```

Expected: NEUROS enters HYPOTHESIS mode, forms testable theories, proposes experiments.

### Example 3: Action Planning (COACH Mode)
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Help me create a morning routine to optimize my energy",
    "session_id": "coach-session-003",
    "user_id": "user123"
  }'
```

Expected: NEUROS enters COACH mode, provides numbered action items, specific protocols.

---

## 🔧 Configuration

### Mode Confidence Scoring
The system uses sophisticated scoring algorithms for each mode:

```python
# COMPANION mode scoring considers:
- Emotional word frequency
- Stress indicator trends
- Support request patterns

# HYPOTHESIS mode scoring considers:
- Curiosity indicators
- Pattern-seeking language
- Current conversation phase

# Each mode has unique scoring logic
```

### Memory Configuration
```python
# L1 Memory (Real-time)
- TTL: 2 hours
- Storage: Redis
- Updates: Every interaction

# L2 Memory (Working)
- TTL: 24 hours
- Storage: Redis
- Updates: Pattern-based

# L3 Memory (Long-term)
- TTL: Permanent
- Storage: PostgreSQL
- Updates: Significant insights only
```

---

## 🧪 Testing the Implementation

### 1. Mode Switching Test
Send messages that should trigger different modes:
- Stress language → COMPANION
- "Why" questions → HYPOTHESIS
- "Help me plan" → COACH
- "Show me patterns" → SYNTHESIS

### 2. Memory Persistence Test
1. Start a conversation
2. Wait 5 minutes
3. Continue conversation
4. Verify NEUROS remembers context

### 3. Pattern Recognition Test
1. Send similar concerns over multiple sessions
2. Watch for NEUROS identifying patterns
3. Check if hypotheses are generated

---

## 📊 Monitoring

### Key Metrics to Track
- Mode distribution over time
- Average confidence scores
- Pattern strength trends
- Memory tier utilization
- Response generation time

### Logs to Monitor
```bash
# NEUROS logs
docker logs -f neuros-api

# Mode transitions
docker logs neuros-api | grep "Mode selected"

# Memory operations
docker logs neuros-api | grep "Memory"
```

---

## 🚨 Troubleshooting

### Issue: NEUROS not responding
1. Check OpenAI API key is set correctly
2. Verify Redis connection
3. Check PostgreSQL is accessible
4. Review logs for errors

### Issue: Mode not switching appropriately
1. Check mode confidence scores in response
2. Review trigger words in message
3. Verify memory context is loading

### Issue: Memory not persisting
1. Check Redis connection
2. Verify TTL settings
3. Ensure PostgreSQL checkpointer is initialized

---

## 🔮 Future Enhancements

1. **Biometric Integration**
   - Real-time HRV analysis
   - Sleep quality correlation
   - Stress marker trends

2. **Multi-Agent Collaboration**
   - Integrate with other AUREN agents
   - Shared memory pool
   - Collaborative hypothesis generation

3. **Advanced Pattern Recognition**
   - ML-based pattern detection
   - Predictive modeling
   - Anomaly detection

4. **Voice Integration**
   - Whisper API for transcription
   - Emotional tone analysis
   - Voice biomarkers

---

## 📝 Development Notes

### Adding New Modes
1. Add to NEUROSMode enum
2. Create scoring function
3. Add mode instruction
4. Update mode descriptions

### Extending Memory Tiers
1. Define new tier in MemoryTier enum
2. Add to NEUROSState
3. Implement integration logic
4. Update memory update node

### Customizing Personality
1. Edit neuros_agent_profile.yaml
2. Rebuild system prompt
3. Test mode responses
4. Adjust scoring if needed

---

*This implementation represents the pinnacle of NEUROS development, combining sophisticated AI with deep psychological understanding and real-time adaptation.* 