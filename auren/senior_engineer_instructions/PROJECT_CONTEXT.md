# PROJECT CONTEXT

## 🏗️ AUREN 2.0 ARCHITECTURE OVERVIEW

*This file contains domain knowledge, architectural decisions, and project context that Claude should understand when working on the AUREN 2.0 framework.*

---

## 🎯 PROJECT MISSION

**AUREN 2.0**: A production-grade biometric optimization framework designed to process real-time biometric data and provide intelligent health insights through advanced AI agents.

### Core Objectives
- **Real-time Processing**: Handle biometric data streams with minimal latency
- **95% Accuracy**: Maintain high accuracy in biometric analysis and recommendations
- **Enterprise Security**: Implement bank-grade security for sensitive health data
- **Scalable Architecture**: Support multi-tenant operations and horizontal scaling
- **Intelligent Insights**: Provide actionable health optimization recommendations

---

## 🧠 DOMAIN KNOWLEDGE

### Biometric Data Types
*To be populated by Senior Engineer*

### Health Optimization Protocols
*To be populated by Senior Engineer*

### Target User Personas
*To be populated by Senior Engineer*

---

## 🏛️ ARCHITECTURAL DECISIONS

### Technology Stack
- **Backend**: Python with FastAPI/Streamlit
- **Database**: SQLite with ACID transactions (production-grade repository layer)
- **AI Framework**: CrewAI for agent orchestration
- **Biometric Processing**: MediaPipe, dlib for facial analysis
- **Security**: SHA-256 hashing, secure file permissions
- **Communication**: WhatsApp integration for user interaction

### Design Patterns
- **Repository Pattern**: Centralized data access layer
- **Factory Pattern**: Dynamic tool instantiation
- **Protocol Pattern**: Standardized biometric processing workflows
- **Agent Pattern**: Specialized AI agents for different health domains

### Key Protocols
1. **JOURNAL Protocol**: *[Details to be added by Senior Engineer]*
2. **MIRAGE Protocol**: *[Details to be added by Senior Engineer]*
3. **VISOR Protocol**: Visual analysis with SHA-256 security

---

## 🔧 TECHNICAL CONSTRAINTS

### Performance Requirements
- Real-time biometric processing (< 100ms latency)
- Support for concurrent user sessions
- Efficient memory usage for large datasets
- Optimized database queries

### Security Requirements
- No MD5 hashing (SHA-256 minimum)
- Secure file permissions (750/700)
- Input validation and sanitization
- Audit logging for security events

### Quality Standards
- 80% minimum test coverage
- Comprehensive error handling
- Type hints throughout codebase
- Production-ready logging

---

## 🌐 INTEGRATION POINTS

### External Services
- **WhatsApp API**: User communication and data collection
- **Biometric Sensors**: Real-time data ingestion
- **Cloud Storage**: Secure data backup and archival
- **Monitoring Systems**: Performance and health metrics

### Internal Components
- **Agent Factory**: Dynamic agent creation and management
- **Protocol Engine**: Biometric processing workflows
- **Repository Layer**: Data persistence and retrieval
- **Security Layer**: Authentication and authorization

---

## 📊 DATA FLOW

### High-Level Flow
*To be documented by Senior Engineer*

### Critical Paths
*To be identified and documented*

### Error Handling Strategies
*To be defined by Senior Engineer*

---

## 🚀 DEPLOYMENT CONSIDERATIONS

### Environment Requirements
*To be specified by Senior Engineer*

### Scaling Strategies
*To be planned by Senior Engineer*

### Monitoring & Alerting
*To be configured by Senior Engineer*

---

## 📚 BUSINESS CONTEXT

### Market Position
*To be defined by Senior Engineer*

### Competitive Advantages
*To be documented by Senior Engineer*

### Success Metrics
*To be established by Senior Engineer*

---

## 🔮 FUTURE ROADMAP

### Planned Features
*To be outlined by Senior Engineer*

### Technical Debt
*To be tracked and prioritized*

### Innovation Opportunities
*To be explored and evaluated*

---

*This document should be regularly updated by the Senior Engineer to ensure Claude has the most current project context and domain knowledge.*

---

*Last Updated: [To be updated by Senior Engineer]*
*Next Review: [To be scheduled]* 