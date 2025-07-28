# AUREN INFRASTRUCTURE ARCHITECTURE

## Complete Technical Architecture on DigitalOcean

---

## 🏗️ System Architecture Overview

### High-Level Architecture
```
┌──────────────────────────────────────────────────────────────┐
│                         INTERNET                              │
└────────────────────────┬─────────────────────────────────────┘
                         │
                    ┌────▼────┐
                    │ Cloudflare│ (DNS)
                    └────┬────┘
                         │ aupex.ai
                    ┌────▼────────────────────────┐
                    │  DigitalOcean Firewall      │
                    │  - Port 80 (HTTP)           │
                    │  - Port 443 (HTTPS)         │
                    │  - Port 22 (SSH)            │
                    │  - Port 8081 (Kafka UI)     │
                    └────┬────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│              DigitalOcean Droplet (144.126.215.218)          │
│                    Ubuntu 22.04 LTS                          │
├──────────────────────────────────────────────────────────────┤
│                    Docker Engine 24.x                         │
├──────────────────────────────────────────────────────────────┤
│                  Docker Compose V2                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Docker Network: auren-network           │    │
│  │  ┌─────────┐  ┌──────────┐  ┌────────────────┐    │    │
│  │  │  Nginx  │◄─┤ AUREN API│◄─┤  PostgreSQL    │    │    │
│  │  │  :80    │  │  :8080   │  │  :5432         │    │    │
│  │  └─────────┘  └──────────┘  └────────────────┘    │    │
│  │       ▲             │               ▲               │    │
│  │       │             ▼               │               │    │
│  │  ┌─────────┐  ┌──────────┐  ┌─────▼──────┐       │    │
│  │  │ Website │  │  Redis   │  │  ChromaDB  │       │    │
│  │  │  Files  │  │  :6379   │  │   :8000    │       │    │
│  │  └─────────┘  └──────────┘  └────────────┘       │    │
│  │                     │                               │    │
│  │  ┌─────────────────▼───────────────────────┐      │    │
│  │  │         Kafka Ecosystem                  │      │    │
│  │  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ │      │    │
│  │  │  │Zookeeper│ │  Kafka  │ │ Kafka UI │ │      │    │
│  │  │  │  :2181  │ │  :9092  │ │  :8081   │ │      │    │
│  │  │  └─────────┘ └─────────┘ └──────────┘ │      │    │
│  │  └──────────────────────────────────────────┘      │    │
│  │                                                     │    │
│  │  ┌─────────────────┐  ┌──────────────────┐       │    │
│  │  │ Biometric Bridge│  │ Future Services  │       │    │
│  │  │   (LangGraph)   │  │  - Prometheus    │       │    │
│  │  │     :8002       │  │  - Grafana       │       │    │
│  │  └─────────────────┘  └──────────────────┘       │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🌐 Network Architecture

### External Network
- **Public IP**: 144.126.215.218
- **Domain**: aupex.ai
- **DNS Provider**: Cloudflare
- **SSL**: Let's Encrypt (ready to activate)

### Internal Docker Network
- **Network Name**: auren-network
- **Driver**: bridge
- **Subnet**: 172.18.0.0/16 (Docker managed)

### Service Communication Matrix
| From Service | To Service | Port | Protocol | Purpose |
|--------------|------------|------|----------|---------|
| Nginx | AUREN API | 8080 | HTTP | API proxy |
| AUREN API | PostgreSQL | 5432 | TCP | Database queries |
| AUREN API | Redis | 6379 | TCP | Cache/hot memory |
| AUREN API | ChromaDB | 8000 | HTTP | Vector search |
| AUREN API | Kafka | 9092 | TCP | Event streaming |
| Biometric Bridge | PostgreSQL | 5432 | TCP | State persistence |
| Biometric Bridge | Redis | 6379 | TCP | Checkpoints |
| Biometric Bridge | Kafka | 9092 | TCP | Event consumption |
| Kafka | Zookeeper | 2181 | TCP | Coordination |

---

## 💾 Data Architecture

### Storage Layers

#### 1. Ephemeral Storage (Container Layer)
- Application code
- Temporary files
- Process logs

#### 2. Volume Storage (Persistent)
```yaml
Volumes:
  postgres_data:    # Database files
  redis-data:       # Redis persistence
  chromadb-data:    # Vector embeddings
  nginx-logs:       # Access/error logs
```

#### 3. Bind Mounts
```yaml
Bind Mounts:
  ./nginx.conf → /etc/nginx/nginx.conf
  ./auren/dashboard_v2 → /usr/share/nginx/html
  ./sql/init → /docker-entrypoint-initdb.d
  ./auren → /app/auren
```

### Data Flow Architecture
```
User Request → Nginx → AUREN API
                           ↓
                    Decision Layer
                    ↙    ↓    ↘
              Redis  PostgreSQL  ChromaDB
              (Hot)   (Warm)     (Cold)
                    ↘    ↓    ↙
                    Response Pipeline
                           ↓
                    Nginx → User
```

---

## 🔐 Security Architecture

### Layer 1: Network Security
```
Internet → Cloudflare (DDoS Protection)
         → DigitalOcean Firewall
         → UFW (Host Firewall)
         → Docker iptables
```

### Layer 2: Application Security
- Nginx rate limiting
- CORS configuration
- Input validation (Pydantic)
- SQL injection prevention
- XSS protection

### Layer 3: Container Security
- Non-root containers
- Read-only filesystems
- Resource limits
- Network isolation
- No privileged mode

### Layer 4: Data Security
- Encryption at rest (prepared)
- TLS in transit (ready)
- Database access control
- Environment variable secrets

---

## 🚀 Deployment Architecture

### CI/CD Pipeline
```
Local Development
       ↓
   Git Push
       ↓
Build & Package
       ↓
SCP to Server
       ↓
Docker Compose Up
       ↓
Health Checks
       ↓
   Live Service
```

### Blue-Green Deployment Capability
```
Current Stack (Blue)     New Stack (Green)
    Running      →      Build in parallel
                        ↓
                   Health check
                        ↓
                   Switch traffic
                        ↓
    Teardown     ←      Running
```

---

## 📊 Monitoring Architecture

### Metrics Collection
```
Docker Containers
       ↓
  cAdvisor (built-in)
       ↓
  Prometheus
       ↓
   Grafana
```

### Log Aggregation
```
Container Logs → Docker → Log Files
                           ↓
                      Log Rotation
                           ↓
                    Analysis/Archive
```

### Health Monitoring
- Container health checks
- API endpoint monitoring
- Resource usage alerts
- Uptime monitoring

---

## ⚡ Performance Architecture

### Caching Strategy
1. **Browser Cache** - Static assets
2. **Nginx Cache** - Proxy cache
3. **Redis Cache** - Application data
4. **Query Cache** - PostgreSQL

### Load Distribution
```
Nginx (Load Balancer)
  ├─→ Static Files (Direct)
  └─→ API Requests → AUREN API
                      ├─→ Redis (Fast)
                      ├─→ PostgreSQL (Structured)
                      └─→ ChromaDB (Semantic)
```

### Optimization Points
- Connection pooling (PostgreSQL)
- Redis pipelining
- Nginx gzip compression
- Docker layer caching
- Async Python (FastAPI)

---

## 🔄 High Availability Design

### Current Setup (Single Node)
- Automatic container restart
- Health check recovery
- Daily backups
- Quick restore procedures

### Future HA Architecture
```
Load Balancer (DO Managed)
     ├─→ Droplet 1 (Primary)
     └─→ Droplet 2 (Secondary)
           ↓
    Shared Storage
    - DO Spaces (Objects)
    - DO Managed Database
```

---

## 📈 Scalability Architecture

### Vertical Scaling Path
Current → Next Steps:
- 2 vCPU → 4 vCPU
- 4GB RAM → 8GB RAM
- 80GB SSD → 160GB SSD

### Horizontal Scaling Options
1. **Service Separation**
   - Database → Managed PostgreSQL
   - Cache → Managed Redis
   - Storage → DO Spaces

2. **Container Orchestration**
   - Docker Swarm (simple)
   - Kubernetes (complex)

3. **Multi-Region**
   - CDN for static assets
   - Read replicas
   - GeoDNS routing

---

## 🔧 Infrastructure as Code

### Current Implementation
```yaml
# docker-compose.prod.yml defines:
- Service definitions
- Network configuration
- Volume management
- Environment variables
- Health checks
- Dependencies
```

### Automation Scripts
```bash
DEPLOY_NOW.sh         # Master deployment
master_deploy.sh      # Orchestration
setup_production.sh   # Environment setup
remote_deploy.sh      # Remote execution
```

---

## 📊 Capacity Planning

### Current Utilization
- CPU: ~60% average
- Memory: ~70% usage
- Storage: ~40% used
- Network: <1% of 4TB

### Growth Projections
```
Users     CPU    Memory   Storage
100       60%    70%      40GB
1,000     80%    85%      80GB
10,000    Need horizontal scaling
```

### Bottleneck Analysis
1. **Memory** - First constraint
2. **CPU** - Second constraint
3. **Storage** - Manageable
4. **Network** - Not a concern

---

## 🎯 Architecture Decisions

### Why Docker Compose?
- Simple orchestration
- Easy local development
- Quick deployment
- Minimal overhead
- Perfect for single node

### Why DigitalOcean?
- Simple infrastructure
- Predictable pricing
- Good performance
- Easy scaling options
- Managed services available

### Why This Stack?
- PostgreSQL: ACID compliance
- Redis: Speed & versatility
- ChromaDB: Vector search
- Kafka: Event streaming
- FastAPI: Modern & fast

---

## 🔮 Future Architecture Evolution

### Phase 1: Current (Monolithic)
- Single droplet
- Docker Compose
- Manual deployment

### Phase 2: Distributed (6 months)
- Multiple droplets
- Managed databases
- CI/CD pipeline
- Container registry

### Phase 3: Cloud Native (1 year)
- Kubernetes
- Service mesh
- GitOps
- Multi-region

---

*This architecture is designed for reliability, performance, and gradual scaling as AUREN grows.* 