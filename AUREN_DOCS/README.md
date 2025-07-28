# AUREN DOCUMENTATION HUB
## Central Repository for All AUREN Documentation

*Last Updated: July 28, 2025*

---

## 📚 Quick Navigation

### 🚀 Getting Started
- ✅ [Credentials Vault](00_QUICK_START/CREDENTIALS_VAULT.md) - All passwords and access info
- ✅ [SSH Access Standard](00_QUICK_START/SSH_ACCESS_STANDARD.md) - How to connect to servers

### 🏗️ Architecture
- ❌ System Overview - **COMING SOON**
- ❌ Component Map - **COMING SOON**

### 🚢 Deployment  
- ✅ [Biometric System Guide](02_DEPLOYMENT/BIOMETRIC_SYSTEM_DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- ✅ [Section 9 Security Guide](../app/SECTION_9_SECURITY_README.md) - Enterprise security enhancement
- ❌ Website Deployment - **COMING SOON**

### 🔧 Operations
- ✅ [Service Access Guide](03_OPERATIONS/SERVICE_ACCESS_GUIDE.md) - All DevOps tools & dashboards
- ✅ [Nginx Configuration](03_OPERATIONS/NGINX_CONFIGURATION.md) - Critical deployment info
- ✅ [Monitoring Quick Start](../MONITORING_QUICK_START.md) - Grafana & Prometheus guide
- ✅ [Docker Navigation Guide](03_OPERATIONS/DOCKER_NAVIGATION_GUIDE.md) - Complete Docker infrastructure guide
- ✅ [Prometheus Troubleshooting](03_OPERATIONS/PROMETHEUS_TROUBLESHOOTING_PLAYBOOK.md) - Step-by-step fix playbook
- ❌ Daily Checklist - **COMING SOON**
- ❌ Troubleshooting - **COMING SOON**

### 💻 Development
- ✅ [NEUROS Memory Enhancement](../NEUROS_MEMORY_ENHANCEMENT_SUMMARY.md) - Memory tier awareness
- ✅ [Memory Management Tools](../auren/tools/memory_management_tools.py) - Implementation examples
- ✅ [Monitoring Guide](03_DEVELOPMENT/MONITORING_GUIDE.md) - Prometheus & Grafana setup
- ❌ Agent Development Guide - **COMING SOON**
- ❌ API Documentation - **COMING SOON**

### 🚨 Critical Issues & Handoffs
- ✅ [Prometheus Issue Report](../PROMETHEUS_ISSUE_FOR_EXECUTIVE_ENGINEER.md) - For Executive Engineer
- ✅ [NEUROS Memory Audit](../NEUROS_MEMORY_TIER_CAPABILITY_AUDIT.md) - Gap analysis
- ✅ [Website Deployment Post-Mortem](../WEBSITE_DEPLOYMENT_POSTMORTEM.md) - Incident analysis

### 📝 Session Reports
- ✅ [July 28, 2025 Work Summary](../JULY_28_2025_WORK_SUMMARY.md) - Complete session report

---

## 📊 Documentation Status Reports

- ✅ [Documentation Status Report](AUREN_DOCUMENTATION_STATUS_REPORT.md) - Complete assessment of all docs
- ✅ [Documentation Organization Guide](DOCUMENTATION_ORGANIZATION_GUIDE.md) - Where everything should live

---

## 🔑 Most Important Documents (WORKING LINKS ONLY)

1. **[CREDENTIALS VAULT](00_QUICK_START/CREDENTIALS_VAULT.md)** - ⚠️ CONFIDENTIAL
   - SSH passwords
   - Database credentials
   - API keys
   - Service endpoints

2. **[Biometric System Deployment](02_DEPLOYMENT/BIOMETRIC_SYSTEM_DEPLOYMENT_GUIDE.md)**
   - Complete guide for Sections 1-8
   - All commands and configurations
   - Troubleshooting steps

3. **[State of Readiness](../auren/AUREN_STATE_OF_READINESS_REPORT.md)**
   - Current system status
   - Deployment progress
   - Next steps

4. **[Section 9 Security Enhancement](../app/SECTION_9_SECURITY_README.md)**
   - API key management
   - PHI encryption
   - HIPAA audit logging
   - Deployment instructions

---

## 📁 Current Folder Status

```
AUREN_DOCS/
├── 00_QUICK_START/          ✅ Has 2 documents
├── 01_ARCHITECTURE/         ✅ Has 1 document
├── 02_DEPLOYMENT/           ✅ Has 1 document  
├── 03_OPERATIONS/           ✅ Has 1 document
└── 04_DEVELOPMENT/          ❌ Empty - needs content
```

---

## 🆕 Recent Updates

### July 28, 2025 (Later in Day)
- ✅ Enhanced NEUROS with complete memory tier awareness (167 lines added to YAML)
- ✅ Created memory management tools for three-tier system
- ✅ Deployed Prometheus & Grafana monitoring (needs instrumentation fix)
- ✅ Fixed ChromaDB NumPy 2.0 compatibility issue
- ✅ Fixed Level 1 knowledge directory path (removed spaces)
- ✅ Updated Documentation Organization Guide with data flow
- ✅ Created handoff documents for Executive Engineer

### January 28, 2025
- ✅ Created Section 9 Security Enhancement Layer
- ✅ Added enterprise authentication, PHI encryption, and audit logging
- ✅ Updated credentials vault with security keys
- ✅ Created deployment script and comprehensive tests
- ✅ Fixed website deployment (wrong version was live)
- ✅ Created post-mortem and nginx configuration docs

### July 28, 2025 (Earlier)
- ✅ Deployed Biometric System (Sections 1-8)
- ✅ Created comprehensive deployment documentation
- ✅ Updated State of Readiness report
- ✅ Created centralized credentials vault
- ✅ Established sshpass as standard access method

---

## 📝 DOCUMENTS THAT NEED TO BE CREATED

### High Priority (This Week):
1. **01_ARCHITECTURE/SYSTEM_OVERVIEW.md**
   - High-level system design
   - Component interactions
   - Data flow diagrams

2. **03_OPERATIONS/DAILY_CHECKLIST.md**
   - Morning health checks
   - Service verification steps
   - Log review procedures

3. **03_OPERATIONS/TROUBLESHOOTING.md**
   - Common issues and fixes
   - Service restart procedures
   - Debug commands

4. **04_DEVELOPMENT/API_DOCUMENTATION.md**
   - All endpoints
   - Request/response formats
   - Authentication methods

### Medium Priority (Next 2 Weeks):
1. **01_ARCHITECTURE/COMPONENT_MAP.md**
2. **02_DEPLOYMENT/WEBSITE_DEPLOYMENT.md**
3. **04_DEVELOPMENT/AGENT_DEVELOPMENT_GUIDE.md**
4. **03_OPERATIONS/MONITORING_GUIDE.md**

---

## 🎯 Documentation Priorities

### What's Actually Available NOW:
- ✅ Complete biometric system deployment guide
- ✅ All credentials and access information
- ✅ SSH access standards with sshpass
- ✅ Documentation status assessment
- ✅ Documentation organization guide

### What's Missing (Needs Creation):
- ❌ Architecture documentation
- ❌ Operations runbooks
- ❌ Development guides
- ❌ API documentation
- ❌ Website deployment guide

---

## 📝 Documentation Standards

All documentation should include:
- Clear title and purpose
- Date created/updated
- Author information
- Table of contents (for long docs)
- Code examples
- Troubleshooting section

---

## 🔍 Can't Find Something?

### Existing Documentation:
- **Main Project Status**: `auren/AUREN_STATE_OF_READINESS_REPORT.md`
- **Website Documentation**: `AUPEX_WEBSITE_DOCUMENTATION/`
- **LangGraph Documentation**: `LANGRAF Pivot/`
- **Agent Specific**: `auren/agents/{agent_name}/`

### Need These Created:
- Architecture diagrams
- Daily operations procedures
- API endpoint documentation
- Development guides

---

## 📞 Contact

For documentation questions or updates:
- **Role**: Senior Engineer
- **Project**: AUREN
- **Company**: AUPEX

---

*This is the master index for all AUREN documentation. All links have been verified to work as of July 28, 2025 (5:00 AM UTC).* 