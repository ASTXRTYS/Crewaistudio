# AUPEX.AI API DOCUMENTATION

## API Reference Guide

This document details all available API endpoints for the AUREN system accessible through aupex.ai.

---

## 🌐 Base URL

```
Production: https://aupex.ai/api
Local: http://localhost:8080/api
```

---

## 🔑 Authentication

Currently, the API uses Bearer token authentication for protected endpoints.

```http
Authorization: Bearer <your-token>
```

---

## 📡 Endpoints

### 1. System Status

#### GET /
Returns system status and version information.

**Response:**
```json
{
  "message": "AUREN 2.0 - Biometric Optimization System",
  "version": "2.0.0",
  "status": "operational",
  "timestamp": "2025-01-20T10:00:00Z"
}
```

#### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "protocols": "operational",
    "analyzer": "operational", 
    "crew": "operational",
    "rag": "operational",
    "whatsapp": "operational"
  },
  "timestamp": "2025-01-20T10:00:00Z"
}
```

---

### 2. Memory System

#### GET /api/memory/stats
Get memory system statistics across all tiers.

**Response:**
```json
{
  "hot_tier": {
    "type": "redis",
    "total_keys": 1523,
    "memory_usage_mb": 45.2,
    "hit_rate": 0.89
  },
  "warm_tier": {
    "type": "postgresql",
    "total_memories": 15234,
    "size_mb": 234.5,
    "avg_query_ms": 12.3
  },
  "cold_tier": {
    "type": "chromadb",
    "total_embeddings": 45123,
    "collections": 5,
    "avg_search_ms": 145.6
  }
}
```

#### GET /api/memory/agent/{agent_id}/stats
Get memory statistics for a specific agent.

**Parameters:**
- `agent_id` (path) - The agent identifier (e.g., "neuroscientist")

**Response:**
```json
{
  "agent_id": "neuroscientist",
  "memories": {
    "total": 3421,
    "recent": 45,
    "categories": {
      "protocols": 1234,
      "insights": 892,
      "hypotheses": 1295
    }
  },
  "last_access": "2025-01-20T09:55:00Z"
}
```

#### GET /api/memory/recent
Get recent memory operations.

**Query Parameters:**
- `limit` (optional) - Number of results (default: 20)
- `agent_id` (optional) - Filter by agent

**Response:**
```json
{
  "memories": [
    {
      "id": "mem_123",
      "agent_id": "neuroscientist",
      "type": "insight",
      "content": "HRV pattern indicates stress response",
      "timestamp": "2025-01-20T09:50:00Z",
      "confidence": 0.87
    }
  ]
}
```

---

### 3. Knowledge Graph

#### GET /api/knowledge-graph/data
Retrieve knowledge graph visualization data.

**Query Parameters:**
- `agent_id` (optional) - Filter by agent
- `depth` (optional) - Graph depth (default: 2)
- `limit` (optional) - Max nodes (default: 100)

**Response:**
```json
{
  "nodes": [
    {
      "id": "node_1",
      "label": "HRV Analysis",
      "type": "concept",
      "agent": "neuroscientist",
      "importance": 0.9
    }
  ],
  "links": [
    {
      "source": "node_1",
      "target": "node_2",
      "type": "relates_to",
      "strength": 0.75
    }
  ],
  "metadata": {
    "total_nodes": 156,
    "total_links": 423,
    "last_updated": "2025-01-20T09:45:00Z"
  }
}
```

#### POST /api/knowledge-graph/access
Record knowledge access event for tracking.

**Request Body:**
```json
{
  "node_id": "node_123",
  "agent_id": "neuroscientist",
  "access_type": "read",
  "context": "hypothesis_validation"
}
```

**Response:**
```json
{
  "status": "recorded",
  "access_id": "acc_456",
  "timestamp": "2025-01-20T10:00:00Z"
}
```

---

### 4. Agent Management

#### GET /api/agent-cards/{agent_id}
Get detailed information for a specific agent.

**Parameters:**
- `agent_id` (path) - The agent identifier

**Response:**
```json
{
  "agent_id": "neuroscientist",
  "name": "Dr. Neural",
  "status": "active",
  "specialization": "CNS optimization",
  "metrics": {
    "interactions_today": 45,
    "hypotheses_generated": 12,
    "success_rate": 0.89
  },
  "current_focus": "HRV pattern analysis",
  "recent_insights": [
    {
      "id": "ins_123",
      "content": "Detected correlation between sleep quality and HRV",
      "confidence": 0.92,
      "timestamp": "2025-01-20T08:30:00Z"
    }
  ]
}
```

---

### 5. Protocol Management

#### POST /api/protocols/{protocol}/entry
Create an entry in a specific protocol.

**Parameters:**
- `protocol` (path) - Protocol name (journal, mirage, visor)

**Request Body:**
```json
{
  "user_id": "user_123",
  "data": {
    "hrv": 65,
    "stress_level": 3,
    "notes": "Feeling good after meditation"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "entry": {
    "id": "entry_789",
    "protocol": "journal",
    "timestamp": "2025-01-20T10:00:00Z"
  }
}
```

---

### 6. Biometric Analysis

#### POST /api/biometric/analyze
Analyze biometric data for insights.

**Request Body:**
```json
{
  "user_id": "user_123",
  "biometrics": {
    "hrv": 58,
    "heart_rate": 72,
    "temperature": 36.5,
    "stress_score": 4
  },
  "context": {
    "activity": "working",
    "time_of_day": "morning"
  }
}
```

**Response:**
```json
{
  "analysis": {
    "status": "normal",
    "insights": [
      "HRV within healthy range",
      "Slight elevation in stress"
    ],
    "recommendations": [
      "Consider a 5-minute breathing exercise"
    ],
    "confidence": 0.85
  }
}
```

---

### 7. AI Crew Processing

#### POST /api/crew/process
Process data through the multi-agent crew.

**Request Body:**
```json
{
  "user_id": "user_123",
  "request_type": "daily_update",
  "data": {
    "biometrics": {...},
    "activities": [...],
    "goals": [...]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "crew_analysis": {
    "participating_agents": ["neuroscientist", "coach"],
    "consensus": "Recommend rest day",
    "individual_insights": {
      "neuroscientist": "Neural fatigue detected",
      "coach": "Recovery needed for optimal performance"
    }
  }
}
```

---

### 8. RAG System

#### POST /api/rag/query
Query the Retrieval-Augmented Generation system.

**Request Body:**
```json
{
  "query": "What are the best protocols for improving HRV?",
  "context": {
    "user_profile": "athlete",
    "current_hrv": 55
  },
  "urgency": "normal"
}
```

**Response:**
```json
{
  "status": "success",
  "query": "What are the best protocols for improving HRV?",
  "results": {
    "answer": "Based on your profile...",
    "sources": [
      {
        "protocol": "VISOR",
        "relevance": 0.92
      }
    ],
    "confidence": 0.88
  }
}
```

---

### 9. WebSocket Endpoints

#### WS /ws/dashboard/{user_id}
Real-time dashboard updates.

**Connection:**
```javascript
const ws = new WebSocket('ws://aupex.ai/ws/dashboard/user_123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

**Message Types:**
```json
// Memory update
{
  "type": "memory_update",
  "tier": "hot",
  "agent": "neuroscientist",
  "data": {...}
}

// Agent status
{
  "type": "agent_status",
  "agent_id": "neuroscientist",
  "status": "processing",
  "current_task": "analyzing biometrics"
}

// Breakthrough alert
{
  "type": "breakthrough",
  "agent": "neuroscientist",
  "insight": "New pattern discovered",
  "importance": 0.95
}
```

#### WS /ws/anomaly/{agent_id}
Real-time anomaly detection stream.

**Message Types:**
```json
{
  "type": "anomaly_detected",
  "severity": "medium",
  "description": "Unusual HRV pattern",
  "recommended_action": "Manual review",
  "timestamp": "2025-01-20T10:00:00Z"
}
```

---

### 10. WhatsApp Integration

#### POST /api/whatsapp/webhook
WhatsApp webhook for incoming messages.

**Note:** This endpoint is used by WhatsApp Business API only.

#### POST /api/whatsapp/send
Send a WhatsApp message.

**Request Body:**
```json
{
  "to": "+1234567890",
  "message": "Your HRV analysis is ready",
  "template": "analysis_complete"
}
```

---

## 🔒 Error Responses

All endpoints return standard error responses:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Description of the error",
    "details": {...}
  },
  "status": 400
}
```

### Common Error Codes:
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error

---

## 📊 Rate Limiting

API requests are rate limited:
- **Anonymous**: 100 requests/hour
- **Authenticated**: 1000 requests/hour
- **WebSocket**: No limit on messages

Headers returned:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1516239022
```

---

## 🧪 Testing

### Using cURL:
```bash
# Get health status
curl https://aupex.ai/api/health

# Get memory stats
curl -H "Authorization: Bearer token" \
  https://aupex.ai/api/memory/stats

# Query knowledge graph
curl "https://aupex.ai/api/knowledge-graph/data?depth=2&limit=50"
```

### Using JavaScript:
```javascript
// Fetch API example
const response = await fetch('https://aupex.ai/api/health');
const data = await response.json();
console.log(data);

// WebSocket example
const ws = new WebSocket('wss://aupex.ai/ws/dashboard/user_123');
ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

---

## 📝 Notes

1. All timestamps are in ISO 8601 format (UTC)
2. Request/response bodies are JSON
3. WebSocket messages are JSON-encoded
4. API versioning through headers (future)
5. CORS enabled for web clients

---

*Last Updated: January 20, 2025*  
*API Version: 2.0.0* 