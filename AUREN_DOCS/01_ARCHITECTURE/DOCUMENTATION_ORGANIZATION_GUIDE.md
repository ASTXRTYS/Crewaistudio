# AUREN DOCUMENTATION ORGANIZATION GUIDE
## Where Everything Should Live

*Created: July 28, 2025*

---

## 📁 RECOMMENDED DOCUMENTATION STRUCTURE

```
CrewAI-Studio-main/
│
├── AUREN_DOCS/                    # Master documentation hub
│   ├── 00_QUICK_START/
│   │   ├── CREDENTIALS_VAULT.md   # All passwords/access (SECURE)
│   │   └── SSH_ACCESS_STANDARD.md # sshpass usage guide
│   │
│   ├── 01_ARCHITECTURE/
│   │   └── DOCUMENTATION_ORGANIZATION_GUIDE.md  # This file - table of contents
│   │
│   ├── 02_DEPLOYMENT/
│   │   ├── BIOMETRIC_SYSTEM_DEPLOYMENT_GUIDE.md  ✅ Complete deployment guide
│   │   ├── SECTION_11_ENHANCEMENT_GUIDE.md      ✅ Event sourcing & real-time
│   │   └── SECTION_12_MAIN_EXECUTION_GUIDE.md   ✅ Production runtime layer
│   │
│   ├── 03_OPERATIONS/
│   │   ├── SERVICE_ACCESS_GUIDE.md   ✅ All DevOps tools
│   │   ├── NGINX_CONFIGURATION.md    ✅ Website deployment
│   │   ├── DOCKER_NAVIGATION_GUIDE.md ✅ Container navigation & troubleshooting
│   │   ├── PROMETHEUS_TROUBLESHOOTING_PLAYBOOK.md ✅ Prometheus fix history
│   │   ├── METRICS_CATALOG.md      ✅ Complete AUREN metrics reference
│   │   ├── GRAFANA_QUERY_LIBRARY.md ✅ Ready-to-use PromQL queries
│   │   ├── OBSERVABILITY_RUNBOOK.md ✅ Daily monitoring procedures
│   │   └── MONITORING_STABILITY_GUIDE.md ✅ Prevention & recovery procedures
│   │
│   ├── 04_DEVELOPMENT/
│   │   ├── MONITORING_GUIDE.md      ✅ Complete monitoring setup
│   │   └── INTEGRATION_PATTERNS.md  ✅ Best practices for new features
│   │
│   └── README.md                  # Navigation hub with all links
│
├── app/                           # Application UI and integration
│   ├── biometric_security_integration.py  # Section 9 example
│   ├── section_9_security.py      # Security module
│   └── SECTION_9_SECURITY_README.md  # Security documentation
│
├── auren/                         # Main AUREN application
│   ├── agents/                    # Agent implementations
│   │   └── neuros/               # NEUROS agent files
│   ├── api/                      # API services
│   ├── biometric/                # Biometric processing
│   ├── config/                   # Agent configurations
│   │   └── neuros.yaml           ✅ ENHANCED with memory awareness
│   ├── dashboard/                # Visualization dashboards
│   ├── src/                      # Source code
│   │   └── agents/
│   │       └── level1_knowledge/ # NEUROS knowledge base
│   ├── tools/                    # Agent tools
│   │   └── memory_management_tools.py  ✅ Memory tier management
│   └── AUREN_STATE_OF_READINESS_REPORT.md  ✅ Current status
│
├── config/                        # CrewAI configurations
│   └── agents/                   # Agent YAML profiles
│
├── scripts/                       # Deployment and utility scripts
│   ├── deploy_section_9_security.sh
│   ├── deploy_monitoring_stack.sh
│   ├── fix_chromadb.sh
│   └── [many more deployment scripts]
│
├── migrations/                    # Database migrations
│   └── add_security_tables.sql   # Section 9 schema
│
├── sql/                           # Database initialization
│   └── init/                     # Schema files
│
├── tests/                         # Test suites
│   └── test_section_9_security.py
│
├── AUPEX_WEBSITE_DOCUMENTATION/   ✅ Website documentation
│   ├── 01_Architecture/
│   ├── 02_Implementation/
│   ├── 03_Deployment/
│   ├── 04_Configuration/
│   └── 05_Status_Reports/
│
├── DIGITALOCEAN_DOCKER_INFRASTRUCTURE/  # Infrastructure docs
│   ├── 01_Infrastructure_Overview/
│   ├── 02_Docker_Services/
│   ├── 03_Server_Configuration/
│   ├── 04_Deployment_Scripts/
│   └── 05_Monitoring_Maintenance/
│
├── LANGRAF Pivot/                 # Strategic planning
│   ├── 01_Migration_Planning/
│   ├── 02_Current_State/
│   ├── 03_Implementation_Examples/
│   └── 04_Knowledge_Base/
│
└── [Root Level Documents]
    ├── CURRENT_PRIORITIES.md      # Active task tracking
    ├── PROMETHEUS_ISSUE_FOR_EXECUTIVE_ENGINEER.md
    ├── NEUROS_MEMORY_TIER_CAPABILITY_AUDIT.md
    ├── NEUROS_MEMORY_ENHANCEMENT_SUMMARY.md
    ├── SECTION_9_INTEGRATION_STATUS.md
    ├── MONITORING_QUICK_START.md
    └── JULY_28_2025_WORK_SUMMARY.md
```

---

## 📊 CURRENT DOCUMENTATION STATUS

### Folder Document Counts:
- `00_QUICK_START/`: 2 documents ✅
- `01_ARCHITECTURE/`: 1 document ✅
- `02_DEPLOYMENT/`: 4 documents ✅ (Section 11 & 12 added!)
- `03_OPERATIONS/`: 8 documents ✅ (Significantly expanded!)
- `04_ARCHITECTURE/`: 1 document ✅ (Migration tracking!)
- `04_DEVELOPMENT/`: 2 documents ✅

**Total AUREN_DOCS**: 18 documents

### Recent Additions (January 29, 2025):
- Added Section 12 Main Execution Guide (production runtime)
- Added Section 11 deployment and testing scripts
- Created deployment summary for partial implementation
- Added event sourcing demo script
- Updated State of Readiness (93% → preparing for 100%)
- Created CrewAI to LangGraph Migration Status document
- Updated Section 12 status (paused pending migration)

### Recent Additions (January 28, 2025):
- Added comprehensive monitoring documentation
- Created metrics catalog and query library
- Added observability runbook and stability guide
- Created integration patterns for developers

---

## 📋 DOCUMENTATION BY PURPOSE

### 1. **Access & Credentials**
**Location**: `AUREN_DOCS/00_QUICK_START/CREDENTIALS_VAULT.md`
- All passwords
- API keys
- Server access
- Database credentials

### 2. **System Status & Progress**
**Location**: `auren/AUREN_STATE_OF_READINESS_REPORT.md`
- Current deployment status
- Completion percentages
- Recent updates
- Next steps

### 3. **Deployment Procedures**
**Location**: `AUREN_DOCS/02_DEPLOYMENT/`
- Step-by-step deployment guides
- Docker configurations
- Environment setup
- Infrastructure requirements

### 4. **Agent Documentation**
**Location**: `auren/agents/{agent_name}/`
- Each agent gets its own folder
- README.md for overview
- DEPLOYMENT_GUIDE.md for setup
- API_REFERENCE.md for endpoints

**NEUROS Configuration**: `auren/config/neuros.yaml`
- Complete personality definition
- 5 cognitive modes (baseline/reflex/hypothesis/companion/sentinel)
- Decision thresholds and rules
- **ENHANCED**: Full three-tier memory system awareness (July 28, 2025)

**NEUROS Level 1 Knowledge**: `auren/src/agents/level1_knowledge/`
- 15 knowledge files for CNS optimization
- Core protocols and thresholds
- Evidence-based guidelines
- **NOTE**: Fixed from "Level 1 knowledge " (with spaces)

**NEUROS Memory Tools**: `auren/tools/memory_management_tools.py`
- 5 essential memory management functions
- Implementation examples for tier operations
- Created July 28, 2025

### 5. **Operational Procedures**
**Location**: `AUREN_DOCS/03_OPERATIONS/`
- Daily/weekly checklists
- Monitoring procedures
- Troubleshooting guides
- Emergency contacts

### 6. **Data Flow Architecture**
**Biometric Data Flow**:
```
Wearables → Webhooks → Biometric API (port 8888) → Kafka → PostgreSQL/TimescaleDB
                                                        ↓
                                                   AI Agent (NEUROS)
                                                        ↓
                                                Frontend Dashboard
```

**Memory System** (`auren/THREE_TIER_MEMORY_IMPLEMENTATION.md`):
- **Redis (Hot Tier)**: Recent interactions < 30 days
- **PostgreSQL (Warm Tier)**: Structured storage 30 days - 1 year  
- **ChromaDB (Cold Tier)**: Semantic search > 1 year
- **NOTE**: Level 1 knowledge is loaded into ChromaDB (cold tier) for semantic search

**Monitoring Flow**:
```
All Services → Metric Exporters → Prometheus → Grafana
```

### 6. **Deployment Scripts & Tools**
**Location**: `scripts/`

**Security & Infrastructure**:
- `deploy_section_9_security.sh` - Security layer deployment
- `deploy_monitoring_stack.sh` - Prometheus & Grafana deployment
- `fix_chromadb.sh` - ChromaDB NumPy 2.0 compatibility fix
- `fix_prometheus_metrics.sh` & `fix_prometheus_metrics_v2.sh` - Monitoring fix attempts

**API & Integration**:
- `create_device_api_keys.py` - API key generation for devices
- `enable_webhook_signatures.py` - Webhook security guide
- `create_initial_admin_key.py` → `simple_create_admin_key.py` - Admin key creation

---

## 🚀 IMMEDIATE ACTIONS

### 1. Create Master Documentation Folder
```bash
mkdir -p AUREN_DOCS/{00_QUICK_START,01_ARCHITECTURE,02_DEPLOYMENT,03_OPERATIONS,04_DEVELOPMENT}
```

### 2. Move Existing Documentation
```bash
# Move deployment guide
mv BIOMETRIC_SYSTEM_DEPLOYMENT_GUIDE.md AUREN_DOCS/02_DEPLOYMENT/

# Move credentials vault
mv AUREN_CREDENTIALS_VAULT.md AUREN_DOCS/00_QUICK_START/CREDENTIALS_VAULT.md

# Move status report
mv AUREN_DOCUMENTATION_STATUS_REPORT.md AUREN_DOCS/
```

### 3. Create Index Files
Create `README.md` in each folder explaining what goes there

---

## 📝 DOCUMENTATION STANDARDS

### Every Document Should Have:
1. **Title & Purpose** - Clear heading
2. **Date & Author** - When created/updated
3. **Table of Contents** - For long docs
4. **Examples** - Code snippets, commands
5. **Troubleshooting** - Common issues

### Naming Conventions:
- Use UPPERCASE for important docs
- Use underscores for spaces
- Add dates to reports: `REPORT_2025_07_28.md`
- Version critical docs: `API_v2.0.md`

---

## 🔍 WHERE TO FIND THINGS

### Looking for passwords?
→ `AUREN_DOCS/00_QUICK_START/CREDENTIALS_VAULT.md`

### Need deployment steps?
→ `AUREN_DOCS/02_DEPLOYMENT/`

### System not working?
→ `AUREN_DOCS/03_OPERATIONS/TROUBLESHOOTING.md`

### Want to add a feature?
→ `AUREN_DOCS/04_DEVELOPMENT/`

### Current system status?
→ `auren/AUREN_STATE_OF_READINESS_REPORT.md`

### Monitoring & observability?
→ `AUREN_DOCS/03_OPERATIONS/` - Contains all monitoring docs:
  - `METRICS_CATALOG.md` - All AUREN metrics
  - `GRAFANA_QUERY_LIBRARY.md` - PromQL queries
  - `OBSERVABILITY_RUNBOOK.md` - Daily procedures
  - `MONITORING_STABILITY_GUIDE.md` - Prevention & recovery
  - `PROMETHEUS_TROUBLESHOOTING_PLAYBOOK.md` - Fix history

### NEUROS memory configuration?
→ `auren/config/neuros.yaml` & `NEUROS_MEMORY_ENHANCEMENT_SUMMARY.md`

---

## 📊 DOCUMENTATION METRICS

### Current State:
- Total Documents: ~45
- Well Organized: 60%
- Up to Date: 70%
- Easily Findable: 50%

### Target State:
- Total Documents: ~60
- Well Organized: 95%
- Up to Date: 90%
- Easily Findable: 95%

---

## ✅ CHECKLIST FOR DOCUMENTATION

When creating new documentation:
- [ ] Choose correct folder based on purpose
- [ ] Use standard naming convention
- [ ] Include date and author
- [ ] Add to relevant index/README
- [ ] Update AUREN_STATE_OF_READINESS_REPORT if needed
- [ ] Remove any hardcoded passwords
- [ ] Add troubleshooting section
- [ ] Include examples

---

## 🎯 PRIORITY ORDER

1. **CRITICAL**: ~~Move all passwords to CREDENTIALS_VAULT.md~~ ✅ DONE
2. **HIGH**: ~~Create AUREN_DOCS structure~~ ✅ DONE
3. **HIGH**: Document remaining agents
4. **MEDIUM**: ~~Create operational runbooks~~ ✅ DONE (Observability runbook created)
5. **MEDIUM**: Update all deployment guides
6. **LOW**: ~~Add diagrams and visuals~~ ✅ DONE (Docker navigation diagram added)

---

*This guide should be the reference for all documentation organization decisions.* 