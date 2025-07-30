# SOP-003: AUREN MASTER TECHNICAL SPECIFICATION

**Version**: 1.0  
**Last Updated**: January 30, 2025  
**Status**: ✅ LOCKED CONFIGURATION - PRODUCTION READY
**Critical**: This document is the single source of truth for the AUREN system's architecture and configuration. DO NOT MODIFY WITHOUT APPROVAL.

---

## 🎯 PRIMARY REFERENCE

**OPERATIONS GUIDE**: See `SOP-001-MASTER-OPERATIONS-GUIDE.md` for daily procedures, deployment, and troubleshooting.

---

## 1. System Overview

AUREN is a biometric-aware AI health optimization system consisting of:
- **Frontend**: React PWA deployed on Vercel
- **Backend**: Docker-based microservices on DigitalOcean
- **AI Engine**: NEUROS (LangGraph-based reasoning system)
- **Data Pipeline**: Kafka for event streaming
- **Storage**: PostgreSQL (long-term) + Redis (hot cache)
- **Monitoring**: Prometheus + Grafana

### Key Innovation
AUREN remembers user health patterns for years, not just 30 days, using a three-tier memory architecture.

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  Internet (HTTPS)                        │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                 Vercel Edge Network                      │
│  ┌─────────────┐      ┌──────────────────┐             │
│  │  AUREN PWA  │      │  Proxy Rewrites  │             │
│  │   (React)   │ ───> │ /api/neuros/* → :8000          │
│  └─────────────┘      │ /api/biometric/* → :8888       │
│                       └──────────────────┘              │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼ (HTTP - Internal)
┌─────────────────────────────────────────────────────────┐
│         DigitalOcean Server (144.126.215.218)           │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Docker Network: auren-network       │   │
│  │                                                  │   │
│  │  ┌──────────────┐       ┌──────────────┐       │   │
│  │  │    NEUROS    │       │  Biometric   │       │   │
│  │  │    :8000     │ <───> │    :8888     │       │   │
│  │  └──────────────┘       └──────────────┘       │   │
│  │         │                       │                │   │
│  │         ▼                       ▼                │   │
│  │  ┌─────────────────────────────────────┐       │   │
│  │  │          Kafka (Event Bus)          │       │   │
│  │  └─────────────────────────────────────┘       │   │
│  │                    │                            │   │
│  │         ┌──────────┴──────────┐                │   │
│  │         ▼                     ▼                │   │
│  │  ┌──────────────┐     ┌──────────────┐        │   │
│  │  │  PostgreSQL  │     │    Redis     │        │   │
│  │  │    :5432     │     │    :6379     │        │   │
│  │  └──────────────┘     └──────────────┘        │   │
│  │                                                 │   │
│  │  ┌──────────────┐     ┌──────────────┐        │   │
│  │  │  Prometheus  │ <── │   Grafana    │        │   │
│  │  │    :9090     │     │    :3000     │        │   │
│  │  └──────────────┘     └──────────────┘        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 3. Component Details & Configuration Inventory

### Frontend: AUREN PWA
- **Technology**: React 18 + Vite
- **Deployment**: Vercel (https://auren-omacln1ad-jason-madrugas-projects.vercel.app)
- **Environment Variables**:
    - `VITE_API_URL=/api/neuros`
    - `VITE_NEUROS_URL=/api/neuros`
- **Proxy Config (`vercel.json`)**:
  ```json
  {
    "rewrites": [
      { "source": "/api/neuros/:path*", "destination": "http://144.126.215.218:8000/:path*" },
      { "source": "/api/biometric/:path*", "destination": "http://144.126.215.218:8888/:path*" }
    ]
  }
  ```

### Backend Services

#### NEUROS (Port 8000)
- **Container**: `neuros-advanced`
- **Image**: `neuros-advanced:final-v2`
- **Technology**: FastAPI + LangGraph
- **Environment Variables**:
    - `REDIS_URL=redis://auren-redis:6379`
    - `POSTGRES_URL=postgresql://auren_user:auren_password@auren-postgres:5432/auren_production`
    - `KAFKA_BOOTSTRAP_SERVERS=auren-kafka:9092`
- **CORS Configuration**:
  - **Origins**: `https://*.vercel.app`, `http://localhost:3000`, `http://localhost:5173`
  - **Settings**: Credentials `true`, all methods/headers allowed.

#### Biometric Service (Port 8888)
- **Container**: `biometric-production`
- **Image**: `auren_deploy_biometric-bridge:latest`
- **Technology**: FastAPI
- **Integration**: Publishes biometric events to Kafka.

### Data Layer

#### PostgreSQL (Port 5432)
- **Container**: `auren-postgres`
- **Image**: `timescale/timescaledb:latest-pg16`
- **Credentials**: `auren_user` / `auren_password` (See `CREDENTIALS_VAULT.md`)

#### Redis (Port 6379)
- **Container**: `auren-redis`
- **Image**: `redis:7-alpine`

#### Kafka (Port 9092)
- **Container**: `auren-kafka`
- **Image**: `bitnami/kafka:3.5`

## 4. Data Flow

### Conversation Flow
1. User sends message in PWA.
2. Request hits Vercel edge proxy.
3. Vercel rewrites `https://.../api/neuros/*` to `http://144.126.215.218:8000/*`.
4. NEUROS service processes the request via LangGraph, using Redis and PostgreSQL for state.
5. Response is returned through the same proxy path to the user.

### Biometric Flow (Future)
1. Wearable device sends data to the `biometric-production` webhook at port 8888.
2. The service publishes the normalized event to a Kafka topic.
3. A consumer service (part of `neuros-advanced` or separate) ingests the event.
4. Patterns are analyzed and stored in PostgreSQL.

## 5. Network & Security

### Docker Network
- **Name**: `auren-network` (bridge)
- **Subnet**: 172.18.0.0/16
- All backend containers reside on this single, private network.

### Security Model
- **Edge**: HTTPS is enforced by Vercel.
- **Internal**: Communication is over HTTP within the private Docker network.
- **CORS**: The `neuros-advanced` service is configured to only accept cross-origin requests from our specific Vercel and local development domains.
- **Authentication**: Currently disabled for MVP. Future implementation will use JWTs.

---

**END OF SOP-003** 