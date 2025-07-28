# AUPEX.AI WEBSITE ARCHITECTURE OVERVIEW

## Executive Summary

The aupex.ai website is a modern, high-performance web application built with a static-first approach for maximum speed and reliability. It serves as the public-facing interface for the AUREN biometric AI system.

---

## 🏗️ Architecture Principles

### 1. **Static-First Design**
- Pre-rendered HTML pages for instant loading
- No build process required
- Direct deployment of HTML/CSS/JS files
- CDN-friendly architecture

### 2. **Progressive Enhancement**
- Core content works without JavaScript
- Enhanced features (3D, animations) load progressively
- Graceful degradation for older browsers

### 3. **Real-Time Ready**
- WebSocket infrastructure in place
- Event-driven updates prepared
- Streaming data visualization capable

### 4. **Performance Optimized**
- Minimal dependencies
- Lazy loading for heavy resources
- Efficient caching strategies
- Sub-2-second page loads

---

## 🔧 Technology Stack

```
┌─────────────────────────────────────────┐
│           Frontend (Client)              │
├─────────────────────────────────────────┤
│  HTML5 │ CSS3 │ Vanilla JavaScript      │
│  Three.js (3D) │ Canvas API (Charts)    │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│          Web Server (Nginx)              │
├─────────────────────────────────────────┤
│  Static File Serving │ Reverse Proxy     │
│  SSL Termination │ Compression           │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│         Backend Services                 │
├─────────────────────────────────────────┤
│  FastAPI (REST API) │ WebSocket Server   │
│  PostgreSQL │ Redis │ ChromaDB           │
└─────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
auren/dashboard_v2/
├── index.html              # Landing page
├── agents/
│   ├── index.html         # Agent listing
│   └── neuroscientist.html # Agent dashboard
├── styles/
│   ├── main.css           # Global styles
│   └── neuroscientist.css # Page-specific
├── js/
│   ├── main.js            # Homepage logic
│   └── neuroscientist.js  # Dashboard logic
└── public/                # Static assets
    ├── images/
    ├── fonts/
    └── data/
```

---

## 🌐 Request Flow

1. **User visits aupex.ai**
   - DNS resolves to 144.126.215.218
   - Nginx serves static HTML

2. **Page loads resources**
   - CSS files (immediate)
   - JavaScript files (deferred)
   - Third-party libraries (async)

3. **Interactive features initialize**
   - 3D particle system starts
   - WebSocket connection established
   - API data fetched

4. **Real-time updates flow**
   - WebSocket receives events
   - UI updates dynamically
   - Charts refresh with new data

---

## 🔒 Security Architecture

### Current Implementation:
- HTTP serving (port 80)
- API authentication ready
- CORS configured
- Input sanitization

### Planned Enhancements:
- HTTPS with Let's Encrypt
- Content Security Policy
- Rate limiting
- DDoS protection

---

## 🚀 Deployment Architecture

```
Developer Machine
    ↓ (git push)
GitHub Repository
    ↓ (deploy script)
DigitalOcean Droplet
    ↓ (nginx serves)
Global Users
```

### Deployment Process:
1. Code changes committed locally
2. `./deploy_new_website.sh` executed
3. Files transferred via SSH
4. Nginx automatically serves new content
5. No downtime or build process

---

## 📊 Performance Architecture

### Optimization Strategies:
1. **Caching**
   - Browser caching headers
   - Nginx caching
   - CDN potential

2. **Compression**
   - Gzip enabled
   - Image optimization
   - Minification planned

3. **Loading Strategy**
   - Critical CSS inline
   - JavaScript deferred
   - Lazy loading for images

### Current Metrics:
- First Paint: <1s
- Time to Interactive: <2s
- Total Page Size: <500KB (excluding 3D)

---

## 🔄 Integration Points

### 1. **API Integration**
- Base URL: `/api/*`
- Authentication: Bearer tokens
- Format: JSON REST

### 2. **WebSocket Integration**
- Endpoint: `ws://aupex.ai/ws`
- Protocol: JSON messages
- Events: Real-time updates

### 3. **Database Integration**
- PostgreSQL: Persistent data
- Redis: Cache layer
- ChromaDB: Vector search

---

## 🎯 Scalability Considerations

### Horizontal Scaling:
- Static files → CDN distribution
- API calls → Load balancer
- WebSockets → Sticky sessions

### Vertical Scaling:
- Current: 2 vCPU, 4GB RAM
- Can scale to: 8 vCPU, 32GB RAM
- Database: Separate server possible

---

## 🛠️ Development Workflow

1. **Local Development**
   - Edit HTML/CSS/JS directly
   - Python server for testing
   - Live reload capabilities

2. **Testing**
   - Browser testing
   - API integration tests
   - Performance profiling

3. **Deployment**
   - Single command deployment
   - Zero downtime
   - Instant rollback possible

---

## 📈 Future Architecture Evolution

### Phase 1: Foundation (Current)
- Static website ✅
- Basic interactivity ✅
- API integration ✅

### Phase 2: Enhancement
- HTTPS activation
- CDN integration
- Advanced caching

### Phase 3: Scale
- Multi-region deployment
- Microservices architecture
- Kubernetes orchestration

---

*This document provides the high-level view of the aupex.ai architecture. For detailed implementation specifics, refer to WEBSITE_TECHNICAL_ARCHITECTURE.md* 