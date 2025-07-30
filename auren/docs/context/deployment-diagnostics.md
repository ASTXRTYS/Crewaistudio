# PWA + NEUROS Deployment Diagnostic Guide
## Critical Issue Identification Framework

### 🔴 PRIORITY 1: Docker Networking Issues

**SYMPTOMS:**
- `ConnectionError: Error 111 connecting to localhost:6379`
- `[Errno -2] Name or service not known`
- PostgreSQL connection timeouts

**DIAGNOSTIC QUESTIONS:**
1. **Container Communication:**
   ```bash
   # From inside the NEUROS container:
   docker exec -it neuros_container ping redis_db
   docker exec -it neuros_container ping postgres_db
   ```
   **Q: Do these commands succeed?**

2. **Redis Connection String:**
   - Are you using `redis://localhost:6379` or `redis://redis_db:6379`?
   - **CRITICAL:** The `redis-om-python` library ignores connection parameters and looks for `REDIS_OM_URL` environment variable
   ```yaml
   environment:
     - REDIS_OM_URL=redis://redis_db:6379
   ```

3. **PostgreSQL URI Format:**
   - LangGraph expects `DATABASE_URI` not `POSTGRES_URI`
   - Format must include: `autocommit=True` and `row_factory=dict_row`
   ```python
   # ❌ This will fail
   postgresql://user:pass@postgres:5432/db
   
   # ✅ This works
   postgresql://user:pass@postgres:5432/db?autocommit=true
   ```

### 🔴 PRIORITY 2: LangGraph Checkpointing Issues

**SYMPTOMS:**
- Checkpoints not persisting
- `TypeError: tuple indices must be integers or slices, not str`
- Lost conversation state after restart

**DIAGNOSTIC QUESTIONS:**
1. **PostgreSQL Checkpointer Setup:**
   ```python
   # Did you call .setup() on first use?
   checkpointer = PostgresSaver.from_conn_string(DB_URI)
   checkpointer.setup()  # Creates required tables
   ```

2. **Connection Pool Configuration:**
   ```python
   # Are you using a global connection pool?
   from psycopg_pool import AsyncConnectionPool
   
   pool = AsyncConnectionPool(
       conninfo=DB_URI,
       max_size=20,
       # CRITICAL: These parameters
       kwargs={
           "autocommit": True,
           "row_factory": dict_row
       }
   )
   ```

3. **LangGraph Version:**
   ```bash
   pip list | grep langgraph
   ```
   **Q: Is `langgraph-checkpoint-postgres` >= 2.0.23?**

### 🔴 PRIORITY 3: WebSocket Connection Failures

**SYMPTOMS:**
- `WebSocket connection to 'ws://...' failed`
- `An insecure WebSocket connection may not be initiated from a page loaded over HTTPS`
- Connection drops after 30 seconds

**DIAGNOSTIC QUESTIONS:**
1. **HTTPS/WSS Mismatch:**
   - Is your PWA served over HTTPS?
   - Are you trying to connect to `ws://` instead of `wss://`?
   - **Fix:** Use `wss://` for secure WebSocket connections

2. **CORS Configuration:**
   ```python
   # In FastAPI:
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-pwa-domain.com"],
       allow_methods=["*"],
       allow_headers=["*"],
       allow_credentials=True
   )
   ```

3. **Service Worker Limitations:**
   - Service workers CAN'T maintain WebSocket connections when PWA is closed
   - **Q: Are you trying to use WebSockets in the service worker?**

### 🔴 PRIORITY 4: PWA Offline Functionality

**SYMPTOMS:**
- `Uncaught (in promise) TypeError: Failed to fetch`
- PWA not installable due to offline requirements
- Service worker not caching correctly

**DIAGNOSTIC QUESTIONS:**
1. **Service Worker Registration:**
   ```javascript
   // Is this in your main app?
   if ('serviceWorker' in navigator) {
       navigator.serviceWorker.register('/sw.js')
   }
   ```

2. **Cache Strategy:**
   ```javascript
   // In sw.js - Are you caching API responses?
   self.addEventListener('fetch', (event) => {
       // Skip WebSocket requests
       if (event.request.url.startsWith('ws')) return;
       
       event.respondWith(
           caches.match(event.request).then(response => {
               return response || fetch(event.request);
           })
       );
   });
   ```

3. **Offline Fallback:**
   - Do you have an offline.html page cached?
   - Are critical assets in the cache manifest?

### 🔴 PRIORITY 5: Environment Variable Issues

**DIAGNOSTIC QUESTIONS:**
1. **Docker Compose Environment:**
   ```yaml
   # Are these set correctly?
   services:
     neuros:
       environment:
         - OPENAI_API_KEY=${OPENAI_API_KEY}
         - DATABASE_URI=postgresql://...  # NOT POSTGRES_URI
         - REDIS_OM_URL=redis://redis:6379  # NOT localhost
   ```

2. **Port Conflicts:**
   ```bash
   docker ps --format "table {{.Names}}\t{{.Ports}}"
   ```
   **Q: Any port conflicts (5432, 6379, 8000)?**

### 🟡 Quick Fix Checklist

1. **Redis Connection:**
   ```yaml
   # In docker-compose.yml
   environment:
     - REDIS_OM_URL=redis://redis:6379  # MUST use this env var
   ```

2. **PostgreSQL for LangGraph:**
   ```python
   # Connection string format
   DATABASE_URI = "postgresql://user:pass@postgres:5432/db?autocommit=true"
   
   # First time setup
   checkpointer = PostgresSaver.from_conn_string(DATABASE_URI)
   await checkpointer.setup()  # Creates tables
   ```

3. **WebSocket in PWA:**
   ```javascript
   // Use secure WebSocket
   const ws = new WebSocket('wss://your-backend.com/ws');
   
   // Add reconnection logic
   ws.onclose = () => {
       setTimeout(() => connectWebSocket(), 5000);
   };
   ```

4. **Service Worker Fix:**
   ```javascript
   // Skip WebSocket and API calls
   self.addEventListener('fetch', (event) => {
       const url = new URL(event.request.url);
       
       // Don't cache WebSocket or API
       if (url.protocol === 'ws:' || url.protocol === 'wss:' || 
           url.pathname.startsWith('/api/')) {
           return;
       }
       
       // Cache strategy for other resources
       event.respondWith(/* ... */);
   });
   ```

### 🚨 Most Likely Culprits

Based on the patterns, the TOP 3 issues are likely:

1. **Redis connection string** - The library ignores parameters and needs `REDIS_OM_URL`
2. **PostgreSQL checkpointer** - Missing `autocommit=True` or `.setup()` not called
3. **WebSocket HTTPS/WSS mismatch** - PWA on HTTPS trying to connect to `ws://`

### 📋 Information We Need From Senior Engineer

Please ask them to provide:

1. **Error logs:**
   ```bash
   docker logs neuros_container --tail 50
   docker logs redis_container --tail 50
   docker logs postgres_container --tail 50
   ```

2. **Network test from inside container:**
   ```bash
   docker exec -it neuros_container /bin/bash
   # Then inside container:
   nc -zv redis 6379
   nc -zv postgres 5432
   ```

3. **Current docker-compose.yml** (sanitized)

4. **WebSocket connection code** from PWA

5. **Service worker fetch handler**

With these diagnostics, we can pinpoint the exact issue and get your deployment working!