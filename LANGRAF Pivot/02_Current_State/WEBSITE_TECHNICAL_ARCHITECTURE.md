# AUREN Website Technical Architecture Guide
## For Senior Engineers and Technical Teams

---

## 🏗️ Architecture Overview

The AUREN website is a **multi-page, static-first architecture** with real-time capabilities, designed for maximum performance and minimal dependencies.

### Technology Choices & Rationale

| Component | Technology | Why This Choice |
|-----------|------------|-----------------|
| **Frontend Framework** | Vanilla HTML/CSS/JS | No build process, instant deployment, maximum performance |
| **3D Graphics** | Three.js (CDN) | Industry standard for WebGL, excellent documentation |
| **Data Visualization** | Canvas API + D3.js | Fine-grained control, real-time performance |
| **Real-time Comms** | WebSockets | Full-duplex, low latency, native browser support |
| **Styling** | CSS3 with Variables | Modern features, no preprocessor needed |
| **Deployment** | Static files + Nginx | Simple, fast, cacheable, scalable |

---

## 📁 Project Structure

```
auren/dashboard_v2/
├── index.html                  # Landing page
├── agents/
│   ├── index.html             # Agents listing
│   └── neuroscientist.html    # Agent dashboard
├── styles/
│   ├── main.css               # Global styles, design system
│   └── neuroscientist.css     # Agent-specific styles
├── js/
│   ├── main.js                # Homepage animations
│   └── neuroscientist.js      # Dashboard logic
├── public/                    # Static assets (images, fonts)
└── components/                # Future: reusable components
```

---

## 🎨 Design System Implementation

### Color Palette (XAI-Inspired)

```css
:root {
    /* Primary Colors */
    --bg-primary: #000000;        /* Deep space black */
    --bg-secondary: #0a0a0a;      /* Slightly lighter black */
    
    /* Accent Colors */
    --accent-blue: #00D9FF;       /* Electric blue (primary CTA) */
    --accent-purple: #9945FF;     /* Neon purple (secondary) */
    --accent-green: #00FF88;      /* Success/active states */
    
    /* Text Colors */
    --text-primary: #ffffff;      /* High emphasis */
    --text-secondary: #a0a0a0;    /* Medium emphasis */
    
    /* Effects */
    --border-color: rgba(255, 255, 255, 0.1);
    --glow-blue: 0 0 40px rgba(0, 217, 255, 0.5);
    --glow-purple: 0 0 40px rgba(153, 69, 255, 0.5);
}
```

### Typography Scale

```css
/* Font: Inter (Google Fonts) */
--font-h1: 900 6rem/1.1 'Inter';     /* Hero titles */
--font-h2: 900 3rem/1.2 'Inter';     /* Section headers */
--font-h3: 700 1.5rem/1.3 'Inter';   /* Card titles */
--font-body: 400 1rem/1.6 'Inter';   /* Body text */
--font-small: 400 0.875rem/1.5 'Inter'; /* Captions */
```

### Component Patterns

#### Glass Card
```css
.glass-card {
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    transition: all 0.3s ease;
}

.glass-card:hover {
    transform: translateY(-5px);
    border-color: var(--accent-blue);
    box-shadow: var(--glow-blue);
}
```

---

## 🚀 3D Visualization Architecture

### Particle System (Homepage)

```javascript
// Three.js particle system structure
class ParticleSystem {
    constructor() {
        this.particleCount = 5000;
        this.particles = new THREE.BufferGeometry();
        this.material = new THREE.PointsMaterial({
            size: 0.005,
            color: '#00D9FF',
            blending: THREE.AdditiveBlending
        });
    }
    
    // Mouse interaction
    updateMousePosition(mouseX, mouseY) {
        this.mesh.rotation.x += mouseY * 0.001;
        this.mesh.rotation.y += mouseX * 0.001;
    }
}
```

### Knowledge Graph (Neuroscientist Page)

```javascript
// 3D force-directed graph
class KnowledgeGraph3D {
    constructor(container) {
        this.nodes = [];
        this.edges = [];
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, width/height, 0.1, 1000);
    }
    
    addNode(data) {
        const geometry = new THREE.SphereGeometry(0.05, 16, 16);
        const material = new THREE.MeshPhongMaterial({
            color: 0x00D9FF,
            emissive: 0x00D9FF,
            emissiveIntensity: 0.5
        });
        const node = new THREE.Mesh(geometry, material);
        // Position using force-directed layout
        this.nodes.push(node);
        this.scene.add(node);
    }
}
```

---

## 🔌 Real-time Data Integration

### WebSocket Architecture

```javascript
// Enhanced WebSocket connection manager
class RealtimeConnection {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectInterval = 5000;
        this.heartbeatInterval = 30000;
        this.messageHandlers = new Map();
    }
    
    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            console.log('Connected to AUREN backend');
            this.startHeartbeat();
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data.type, data.payload);
        };
        
        this.ws.onclose = () => {
            this.stopHeartbeat();
            setTimeout(() => this.connect(), this.reconnectInterval);
        };
    }
    
    subscribe(messageType, handler) {
        this.messageHandlers.set(messageType, handler);
    }
    
    send(type, payload) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, payload }));
        }
    }
}
```

### Data Flow Pattern

```
Browser <-> WebSocket <-> Nginx <-> FastAPI <-> Services
   |                                              |
   |                                              v
   v                                         PostgreSQL
Three.js                                     Redis
Canvas                                       ChromaDB
```

---

## 🛠️ Development Workflow

### Local Development

```bash
# No build process needed!
# 1. Edit files directly
cd auren/dashboard_v2

# 2. Serve locally (optional)
python -m http.server 8000

# 3. Open browser
open http://localhost:8000
```

### Adding a New Page

1. **Create HTML file**:
```html
<!-- auren/dashboard_v2/technology/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Technology - AUREN</title>
    <link rel="stylesheet" href="../styles/main.css">
    <link rel="stylesheet" href="../styles/technology.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <!-- Include standard navigation -->
    <nav class="main-nav"><!-- ... --></nav>
    
    <!-- Page content -->
    <section class="technology-hero">
        <!-- Your content -->
    </section>
    
    <script src="../js/technology.js"></script>
</body>
</html>
```

2. **Add specific styles** (if needed):
```css
/* styles/technology.css */
.technology-hero {
    /* Page-specific styles */
}
```

3. **Add JavaScript** (if needed):
```javascript
// js/technology.js
document.addEventListener('DOMContentLoaded', () => {
    // Page-specific logic
});
```

### Deployment Process

```bash
# One command deployment
./deploy_new_website.sh

# What happens:
# 1. Creates tarball of dashboard_v2
# 2. Uploads to server via SCP
# 3. Extracts to nginx directory
# 4. Restarts nginx container
# 5. Site is live immediately
```

---

## 🏗️ Server Architecture

### Docker Services

```yaml
# docker-compose.prod.yml (relevant parts)
services:
  nginx:
    image: nginx:alpine
    volumes:
      - ./auren/dashboard_v2:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"
  
  auren-api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name aupex.ai www.aupex.ai;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Compression
    gzip on;
    gzip_types text/css application/javascript;
    
    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://auren-api:8080/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket proxy
    location /ws {
        proxy_pass http://auren-api:8080/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 🔧 Common Tasks

### Update the Navigation

Edit the nav section in each HTML file:
```html
<nav class="main-nav">
    <div class="nav-container">
        <div class="logo">
            <span class="logo-text">AUREN</span>
        </div>
        <div class="nav-links">
            <a href="/" class="nav-link">Home</a>
            <a href="/agents" class="nav-link">Agents</a>
            <!-- Add new link here -->
            <a href="/new-page" class="nav-link">New Page</a>
        </div>
    </div>
</nav>
```

### Add Real-time Data to a Chart

```javascript
// Connect to WebSocket
const ws = new RealtimeConnection('ws://aupex.ai/ws');

// Subscribe to biometric data
ws.subscribe('biometric.hrv', (data) => {
    // Update chart
    hrvChart.addDataPoint(data.timestamp, data.value);
});

// Start connection
ws.connect();
```

### Create a New 3D Visualization

```javascript
// Basic Three.js setup
function create3DVisualization(containerId) {
    const container = document.getElementById(containerId);
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, width/height, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ 
        alpha: true, 
        antialias: true 
    });
    
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);
    
    // Add your 3D objects
    // ...
    
    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        // Update animations
        renderer.render(scene, camera);
    }
    
    animate();
}
```

---

## 🚨 Troubleshooting

### Page shows 403 Forbidden
- Check if the file exists in `auren/dashboard_v2/`
- Ensure proper file permissions
- Verify nginx is serving from correct directory

### 3D animations not working
- Check browser console for errors
- Verify Three.js is loaded from CDN
- Test WebGL support: `window.WebGLRenderingContext`

### WebSocket connection fails
- Check if API service is running
- Verify nginx WebSocket proxy config
- Test with: `wscat -c ws://aupex.ai/ws`

### CSS not updating
- Clear browser cache (Cmd+Shift+R)
- Check if file was deployed
- Verify nginx gzip is working

---

## 📚 Resources

- **Three.js Documentation**: https://threejs.org/docs/
- **WebSocket API**: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- **CSS Custom Properties**: https://developer.mozilla.org/en-US/docs/Web/CSS/--*
- **Nginx Config**: https://nginx.org/en/docs/

---

## 🎯 Next Steps for Engineers

1. **Implement remaining pages** (Technology, Insights, API, About)
2. **Connect real WebSocket data** from FastAPI backend
3. **Add more agent dashboards** as they come online
4. **Optimize 3D performance** for mobile devices
5. **Implement PWA features** for offline capability
6. **Add analytics tracking** (privacy-compliant)
7. **Set up CI/CD pipeline** for automated deployment

---

*This document is maintained by the AUREN engineering team. Last updated: July 27, 2025* 