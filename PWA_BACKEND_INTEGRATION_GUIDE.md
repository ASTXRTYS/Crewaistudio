# PWA BACKEND INTEGRATION GUIDE FOR AUREN
## Comprehensive Technical Specifications for Progressive Web App Development

*Created: January 29, 2025*  
*Author: Senior Engineer*  
*Purpose: Provide Executive Engineer with complete backend integration details for PWA implementation*

---

## 🔌 1. BACKEND INTEGRATION SPECIFICS

### 1.1 Kafka Event Schema

#### User Message Event Structure
```json
{
  "event_type": "user.message",
  "event_id": "ulid_26_chars_here",
  "timestamp": "2025-01-29T21:30:00Z",
  "user_id": "user_123",
  "session_id": "session_abc",
  "message": {
    "text": "How is my HRV trending this week?",
    "context": {
      "device_type": "pwa",
      "agent_requested": "neuros",
      "conversation_id": "conv_xyz"
    }
  },
  "metadata": {
    "ip_address": "192.168.1.1",
    "user_agent": "PWA/1.0",
    "api_key_id": "key_abc123"
  }
}
```

#### Agent Response Event Structure
```json
{
  "event_type": "agent.response",
  "event_id": "ulid_26_chars_here",
  "timestamp": "2025-01-29T21:30:02Z",
  "user_id": "user_123",
  "session_id": "session_abc",
  "conversation_id": "conv_xyz",
  "agent_id": "neuros",
  "response": {
    "text": "Your HRV shows a positive trend...",
    "data": {
      "hrv_7day_avg": 62,
      "trend": "improving",
      "confidence": 0.87
    },
    "visualizations": [
      {
        "type": "line_chart",
        "data_url": "/api/charts/hrv_weekly_123"
      }
    ]
  },
  "processing_time_ms": 245
}
```

#### Biometric Event Schema (Already in Production)
```python
@dataclass
class BiometricEvent:
    device_type: WearableType  # OURA_RING, WHOOP, APPLE_HEALTH, etc.
    user_id: str
    timestamp: datetime
    readings: List[BiometricReading]
    
@dataclass
class BiometricReading:
    type: BiometricType  # HRV, HEART_RATE, SLEEP_QUALITY, etc.
    value: float
    unit: str
    confidence: Optional[float] = None
```

### 1.2 WebSocket Gateway

#### Existing WebSocket Endpoints
```
Production WebSocket Endpoints:
- ws://144.126.215.218:8888/ws/dashboard/{user_id}
- ws://144.126.215.218:8888/ws/anomaly/{agent_id}
```

#### WebSocket Connection Protocol
```javascript
// Connection initialization
const ws = new WebSocket('wss://api.auren.ai/ws/dashboard/user_123');

// Authentication after connection
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    api_key: 'Bearer YOUR_API_KEY',
    session_id: 'session_abc'
  }));
};

// Message types
const messageTypes = {
  // Client → Server
  'auth': 'Authentication',
  'ping': 'Keep-alive',
  'subscribe': 'Subscribe to updates',
  'message': 'User message',
  
  // Server → Client
  'connection': 'Connection established',
  'pong': 'Keep-alive response',
  'agent_response': 'Agent message',
  'biometric_update': 'Real-time biometric data',
  'error': 'Error message'
};
```

### 1.3 Authentication System

#### Current Implementation (Section 9 Security)

**API Key Authentication**:
- Prefix-based O(1) lookup optimization
- Bcrypt hashed keys
- Rate limiting per key
- Role-based access (user/admin)

**API Key Format**:
```
auren_pk_XXXXXXXXXXXXXXXXXXXX  (public key identifier)
auren_sk_YYYYYYYYYYYYYYYYYYYY  (secret key - only shown once)
```

**Authentication Headers**:
```http
Authorization: Bearer auren_sk_YYYYYYYYYYYYYYYYYYYY
X-API-Key: auren_sk_YYYYYYYYYYYYYYYYYYYY  (alternative)
```

**JWT Token Structure** (for session management):
```json
{
  "sub": "user_123",
  "api_key_id": "pk_XXXX",
  "role": "user",
  "exp": 1738188000,
  "iat": 1738184400,
  "session_id": "session_abc"
}
```

---

## 🎨 2. DESIGN SYSTEM DETAILS

### 2.1 AUREN Brand Colors

#### Primary Palette (From Production CSS)
```css
:root {
  /* Core Brand Colors */
  --auren-primary: #00D9FF;      /* Electric Blue */
  --auren-secondary: #9945FF;    /* Neon Purple */
  --auren-success: #00FF88;      /* Success Green */
  
  /* Background Colors */
  --bg-primary: #000000;         /* Deep Space Black */
  --bg-secondary: #0a0a0a;       /* Slightly Lighter Black */
  
  /* Text Colors */
  --text-primary: #ffffff;       /* Pure White */
  --text-secondary: #a0a0a0;     /* Gray */
  
  /* NEUROS Specific (Black Steel Theme) */
  --neuros-black: #0A0A0B;
  --neuros-steel: #1C1E26;
  --neuros-steel-light: #2A2D3A;
  --neuros-space: #0F1419;
  --neuros-accent: #4A9EFF;
  --neuros-neural: #00D4FF;
  --neuros-text: #E7E9EA;
  --neuros-text-dim: #71767B;
}
```

### 2.2 Typography

```css
/* Font Stack */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 
             Roboto, 'Helvetica Neue', Arial, sans-serif;

/* Monospace for Code/Data */
font-family: 'JetBrains Mono', 'Fira Code', Consolas, Monaco, monospace;

/* Font Weights */
--font-regular: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
--font-black: 900;

/* Type Scale */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
--text-5xl: 3rem;      /* 48px */
```

### 2.3 Logo and Assets

**Current Status**: 
- Text-based logo: "AUREN" in bold typography
- No image logo currently deployed
- Favicon: `/img/favicon.ico` (placeholder)

**Recommended Approach for PWA**:
```javascript
// Text Logo Component
const AurenLogo = () => (
  <div className="logo">
    <span className="logo-text">AUREN</span>
    <span className="logo-tagline">Neural Operations</span>
  </div>
);

// CSS for Logo
.logo-text {
  font-size: 2rem;
  font-weight: 900;
  background: linear-gradient(135deg, #00D9FF, #9945FF);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

---

## 🚀 3. DEPLOYMENT ARCHITECTURE

### 3.1 Current Infrastructure

**Production Server**:
- Provider: DigitalOcean
- IP: 144.126.215.218
- OS: Ubuntu 25.04
- Domain: aupex.ai

**Services Running**:
- Nginx (port 80/443)
- Biometric API (port 8888)
- PostgreSQL/TimescaleDB (port 5432)
- Redis (port 6379)
- Kafka (port 9092)
- Prometheus (port 9090)
- Grafana (port 3000)

### 3.2 Recommended PWA Deployment

**Option 1: Vercel (Recommended for PWA)**
```json
// vercel.json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "http://144.126.215.218:8888/:path*"
    },
    {
      "source": "/ws/:path*", 
      "destination": "http://144.126.215.218:8888/ws/:path*"
    }
  ],
  "headers": [
    {
      "source": "/sw.js",
      "headers": [
        {
          "key": "Service-Worker-Allowed",
          "value": "/"
        }
      ]
    }
  ]
}
```

**Option 2: Deploy to Existing Infrastructure**
- Deploy PWA to `/var/www/pwa` on production server
- Configure Nginx subdomain: `pwa.aupex.ai`
- Use existing SSL certificates

### 3.3 SSL/Domain Configuration

**Current SSL**: 
- Domain: aupex.ai
- SSL: Not yet activated (ready for Let's Encrypt)

**PWA Requirements**:
```nginx
# Nginx config for PWA
server {
    listen 443 ssl http2;
    server_name pwa.aupex.ai;
    
    ssl_certificate /etc/letsencrypt/live/aupex.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aupex.ai/privkey.pem;
    
    # PWA headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000";
    
    location / {
        root /var/www/pwa;
        try_files $uri $uri/ /index.html;
    }
}
```

### 3.4 Environment Variables

```bash
# .env.production
NEXT_PUBLIC_API_URL=https://api.aupex.ai
NEXT_PUBLIC_WS_URL=wss://api.aupex.ai/ws
NEXT_PUBLIC_ENVIRONMENT=production

# Backend API Keys (server-side only)
OPENAI_API_KEY=sk-xxxxx
AUREN_API_KEY=auren_sk_xxxxx
DATABASE_URL=postgresql://auren_user:auren_secure_2025@localhost:5432/auren_production
REDIS_URL=redis://localhost:6379/0
```

---

## 🎯 4. SCOPE CLARIFICATION

### 4.1 Agent Prioritization

**Phase 1 (Alpha) - NEUROS Only**:
- Start with NEUROS (formerly Neuroscientist)
- Full CNS optimization capabilities
- HRV analysis, stress detection, recovery protocols

**Phase 2 (Beta) - Additional Agents**:
```yaml
agents:
  nutritionist:
    status: "planned"
    capabilities: ["meal_planning", "macro_tracking", "supplement_advice"]
    
  training_coach:
    status: "planned"
    capabilities: ["workout_programming", "load_management", "performance_tracking"]
    
  sleep_specialist:
    status: "planned"
    capabilities: ["sleep_quality", "circadian_optimization", "recovery_protocols"]
    
  recovery_specialist:
    status: "planned"
    capabilities: ["recovery_strategies", "stress_management", "adaptation_tracking"]
```

### 4.2 User Identification

**For Personal Testing**:
```javascript
// Simple auth for alpha testing
const testUsers = {
  'founder@aupex.ai': {
    user_id: 'user_founder_001',
    role: 'admin',
    api_key: 'auren_sk_test_xxxxx'
  }
};

// Phone-based auth (future)
const phoneAuth = {
  method: 'SMS OTP',
  provider: 'Twilio',
  format: '+1234567890'
};
```

### 4.3 Data Persistence

**Alpha Testing Approach**:
```javascript
// Session storage with 2-hour TTL
const sessionConfig = {
  storage: 'Redis',
  ttl: 7200, // 2 hours
  prefix: 'pwa:session:',
  data: {
    messages: [], // Chat history
    context: {},  // User context
    preferences: {} // UI preferences
  }
};

// No permanent storage for NEUROS conversations
// This preserves NEUROS's core identity constraint
```

---

## 🔧 5. INTEGRATION ENDPOINTS

### 5.1 REST API Endpoints

```typescript
// Base URL: https://api.aupex.ai

// Authentication
POST   /auth/login
POST   /auth/refresh
POST   /auth/logout

// User Profile
GET    /user/profile
PUT    /user/profile
GET    /user/biometrics/summary

// NEUROS Agent
POST   /agents/neuros/chat
GET    /agents/neuros/status
GET    /agents/neuros/specializations

// Biometric Data
GET    /biometrics/readings?start_date=&end_date=&type=
GET    /biometrics/trends/{metric}
GET    /biometrics/anomalies

// WebSocket
WS     /ws/dashboard/{user_id}
WS     /ws/chat/{session_id}
```

### 5.2 GraphQL Schema (Optional Enhancement)

```graphql
type Query {
  user(id: ID!): User
  biometricReadings(userId: ID!, dateRange: DateRange!): [BiometricReading!]!
  agentStatus(agentId: ID!): AgentStatus
}

type Mutation {
  sendMessage(input: MessageInput!): Message!
  updateUserProfile(input: UserProfileInput!): User!
}

type Subscription {
  biometricUpdate(userId: ID!): BiometricReading!
  agentResponse(sessionId: ID!): Message!
}
```

---

## 📦 6. KAFKA TOPICS & STREAMS

### Existing Topics
```bash
# Production Kafka Topics
biometric-events          # All incoming biometric data
biometric-events.dlq      # Dead letter queue
neuros-mode-switches      # NEUROS cognitive mode changes
user-interactions         # User activity tracking
agent-responses           # Agent response events
```

### PWA-Specific Topics
```bash
# New topics for PWA
pwa-user-messages         # Incoming chat messages
pwa-agent-responses       # Outgoing responses
pwa-session-events        # Session lifecycle
pwa-analytics             # Usage analytics
```

---

## 🔒 7. SECURITY CONSIDERATIONS

### 7.1 PWA Security Headers
```javascript
// Security headers for PWA
const securityHeaders = {
  'Content-Security-Policy': "default-src 'self'; connect-src 'self' https://api.aupex.ai wss://api.aupex.ai",
  'X-Frame-Options': 'SAMEORIGIN',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
};
```

### 7.2 API Rate Limiting
```python
# Current rate limits (per API key)
rate_limits = {
    'default': 60,      # requests per minute
    'premium': 300,     # requests per minute
    'admin': 1000      # requests per minute
}
```

---

## 📱 8. PWA MANIFEST

```json
{
  "name": "AUREN Neural Operations",
  "short_name": "AUREN",
  "description": "Elite Neural Operations System",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#000000",
  "theme_color": "#00D9FF",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

---

## 🚨 CRITICAL NOTES

1. **NEUROS Memory Constraint**: Chat sessions MUST NOT persist beyond 2 hours
2. **Production API**: Currently at 144.126.215.218:8888
3. **WebSocket**: Existing implementation uses JSON message protocol
4. **Authentication**: API keys already implemented with rate limiting
5. **SSL Required**: PWA requires HTTPS - activate Let's Encrypt before deployment

---

## 📞 QUICK REFERENCE

### Server Access
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218
```

### Key Files
- Backend API: `auren/api/dashboard_api.py`
- WebSocket: `auren/realtime/enhanced_websocket_streamer.py`
- Security: `app/section_9_security.py`
- NEUROS Config: `auren/config/neuros.yaml`

### Live Endpoints
- API Health: http://144.126.215.218:8888/health
- WebSocket: ws://144.126.215.218:8888/ws/dashboard/{user_id}
- Website: http://aupex.ai

---

*This guide provides all backend integration details needed for PWA development. All information sourced from production deployment documentation and live system configuration.* 