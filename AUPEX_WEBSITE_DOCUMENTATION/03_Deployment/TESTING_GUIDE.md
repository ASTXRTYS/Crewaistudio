# AUPEX.AI TESTING GUIDE

## Complete Testing Procedures for the AUREN Website

This guide covers all testing procedures to ensure aupex.ai functions correctly across all platforms and scenarios.

---

## 🧪 Testing Categories

1. **Functional Testing** - Does everything work?
2. **Performance Testing** - Is it fast enough?
3. **Browser Testing** - Works on all browsers?
4. **Mobile Testing** - Responsive on all devices?
5. **API Testing** - All endpoints functioning?
6. **Security Testing** - Is it secure?

---

## ✅ Functional Testing

### Homepage Tests
```javascript
// Test 1: Page loads successfully
// Expected: Page loads without errors
window.location.href = 'http://aupex.ai';

// Test 2: 3D particles animation starts
// Expected: Canvas element exists and animates
document.querySelector('#particles-canvas') !== null

// Test 3: Navigation works
// Expected: All nav links clickable
document.querySelectorAll('.main-nav a').forEach(link => {
  console.log(link.href, link.textContent);
});

// Test 4: Hero text displays
// Expected: "Understand the Universe Within" visible
document.querySelector('.hero-title').textContent
```

### Agent Pages Tests
```javascript
// Test 1: Agent listing loads
// Navigate to: http://aupex.ai/agents/
// Expected: Grid of agent cards displayed

// Test 2: Neuroscientist dashboard loads
// Navigate to: http://aupex.ai/agents/neuroscientist.html
// Expected: 3D brain model, charts, knowledge graph visible

// Test 3: Real-time charts update
// Expected: Chart values change every few seconds
setInterval(() => {
  console.log('HRV:', document.querySelector('#hrv-value').textContent);
}, 1000);
```

### Interactive Elements
```javascript
// Test 1: 3D models rotate
// Expected: Mouse drag rotates 3D brain
// Action: Click and drag on brain model

// Test 2: Knowledge graph responds
// Expected: Nodes highlight on hover
// Action: Hover over knowledge graph nodes

// Test 3: Hypothesis progress bars
// Expected: Progress bars show animation
// Check: CSS animations running
```

---

## 🚀 Performance Testing

### Page Load Speed
```bash
# Using curl to measure TTFB
time curl -o /dev/null -s -w "%{time_total}\n" http://aupex.ai

# Detailed timing
curl -o /dev/null -s -w "\
DNS Lookup: %{time_namelookup}s\n\
Connect: %{time_connect}s\n\
TTFB: %{time_starttransfer}s\n\
Total: %{time_total}s\n" http://aupex.ai
```

### JavaScript Performance
```javascript
// Test render performance
const startTime = performance.now();

// Force re-render
document.querySelector('#particles-canvas').style.display = 'none';
document.querySelector('#particles-canvas').style.display = 'block';

const endTime = performance.now();
console.log(`Render time: ${endTime - startTime}ms`);

// Monitor FPS
let lastTime = performance.now();
let frames = 0;

function checkFPS() {
  frames++;
  const currentTime = performance.now();
  if (currentTime >= lastTime + 1000) {
    console.log(`FPS: ${frames}`);
    frames = 0;
    lastTime = currentTime;
  }
  requestAnimationFrame(checkFPS);
}
checkFPS();
```

### Resource Loading
```javascript
// Check all resources load
performance.getEntriesByType('resource').forEach(resource => {
  console.log(`${resource.name}: ${resource.duration}ms`);
});

// Check for failed resources
Array.from(document.images).filter(img => !img.complete);
```

---

## 🌐 Browser Compatibility Testing

### Desktop Browsers
Test on these browsers:

#### Chrome (Latest)
```javascript
// Check WebGL support
const canvas = document.createElement('canvas');
const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
console.log('WebGL supported:', !!gl);
```

#### Firefox (Latest)
- Check console for errors
- Verify animations work
- Test developer tools

#### Safari (Latest)
- Check WebSocket compatibility
- Verify CSS animations
- Test on macOS

#### Edge (Latest)
- Verify Chromium features work
- Check performance

### Browser Feature Detection
```javascript
// Feature detection script
const features = {
  webgl: !!document.createElement('canvas').getContext('webgl'),
  websocket: 'WebSocket' in window,
  fetch: 'fetch' in window,
  css_animations: 'animation' in document.body.style,
  backdrop_filter: 'backdropFilter' in document.body.style
};

console.table(features);
```

---

## 📱 Mobile Testing

### Responsive Design Tests

#### iPhone Testing
```javascript
// Simulate iPhone 12
// Chrome DevTools: 390x844

// Test points:
// 1. Navigation menu collapses
// 2. Text remains readable
// 3. 3D elements scale properly
// 4. Touch interactions work
```

#### Android Testing
```javascript
// Simulate Pixel 5
// Chrome DevTools: 393x851

// Additional tests:
// 1. Check Chrome mobile
// 2. Test Samsung Internet
// 3. Verify touch gestures
```

### Mobile Performance
```javascript
// Disable complex animations on mobile
if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
  console.log('Mobile device detected');
  // Check if performance optimizations applied
}
```

### Touch Interaction Tests
```javascript
// Test touch events
document.addEventListener('touchstart', (e) => {
  console.log('Touch detected at:', e.touches[0].clientX, e.touches[0].clientY);
});

// Test swipe gestures
let startX = 0;
document.addEventListener('touchstart', (e) => {
  startX = e.touches[0].clientX;
});

document.addEventListener('touchend', (e) => {
  const endX = e.changedTouches[0].clientX;
  const diff = endX - startX;
  console.log('Swipe distance:', diff);
});
```

---

## 🔌 API Testing

### Basic API Tests
```bash
# Test 1: Health check
curl -i http://aupex.ai/api/health

# Test 2: Memory stats
curl http://aupex.ai/api/memory/stats

# Test 3: Knowledge graph
curl "http://aupex.ai/api/knowledge-graph/data?depth=1"

# Test 4: Agent info
curl http://aupex.ai/api/agent-cards/neuroscientist
```

### API Response Validation
```javascript
// JavaScript API tests
async function testAPIs() {
  const tests = [
    { url: '/api/health', expected: 'status' },
    { url: '/api/memory/stats', expected: 'hot_tier' },
    { url: '/api/knowledge-graph/data', expected: 'nodes' }
  ];

  for (const test of tests) {
    try {
      const response = await fetch(test.url);
      const data = await response.json();
      console.log(`✅ ${test.url}:`, test.expected in data ? 'PASS' : 'FAIL');
    } catch (error) {
      console.log(`❌ ${test.url}: ERROR`, error.message);
    }
  }
}

testAPIs();
```

### WebSocket Testing
```javascript
// Test WebSocket connection
function testWebSocket() {
  const ws = new WebSocket('ws://aupex.ai/ws/dashboard/test');
  
  ws.onopen = () => console.log('✅ WebSocket connected');
  ws.onmessage = (e) => console.log('📨 Message:', e.data);
  ws.onerror = (e) => console.log('❌ WebSocket error:', e);
  ws.onclose = () => console.log('🔌 WebSocket closed');
  
  // Send test message after connection
  setTimeout(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }));
    }
  }, 1000);
}

testWebSocket();
```

---

## 🔒 Security Testing

### Basic Security Checks
```bash
# Check security headers
curl -I http://aupex.ai | grep -E "(X-Frame-Options|X-Content-Type|Strict-Transport)"

# Check for exposed files
curl http://aupex.ai/.git/HEAD
curl http://aupex.ai/.env
curl http://aupex.ai/config.json

# Check CORS headers
curl -H "Origin: http://evil.com" -I http://aupex.ai/api/health
```

### XSS Testing
```javascript
// Test input sanitization
// WARNING: Only test on your own systems
const testPayloads = [
  '<script>alert("XSS")</script>',
  '<img src=x onerror=alert("XSS")>',
  'javascript:alert("XSS")'
];

// Check if inputs are properly escaped
// Should NOT execute any alerts
```

---

## 🔄 Automated Testing

### Simple Test Suite
Create `test_aupex.js`:
```javascript
// Automated test suite
const tests = {
  async checkHomepage() {
    const res = await fetch('http://aupex.ai');
    return res.ok;
  },
  
  async checkAPI() {
    const res = await fetch('http://aupex.ai/api/health');
    const data = await res.json();
    return data.status === 'healthy';
  },
  
  async checkAgentPage() {
    const res = await fetch('http://aupex.ai/agents/neuroscientist.html');
    return res.ok;
  },
  
  async checkWebSocket() {
    return new Promise((resolve) => {
      const ws = new WebSocket('ws://aupex.ai/ws/dashboard/test');
      ws.onopen = () => {
        ws.close();
        resolve(true);
      };
      ws.onerror = () => resolve(false);
      setTimeout(() => resolve(false), 5000);
    });
  }
};

// Run all tests
async function runTests() {
  console.log('🧪 Running AUPEX tests...\n');
  
  for (const [name, test] of Object.entries(tests)) {
    try {
      const result = await test();
      console.log(`${result ? '✅' : '❌'} ${name}`);
    } catch (error) {
      console.log(`❌ ${name} - Error: ${error.message}`);
    }
  }
}

runTests();
```

### Continuous Testing Script
```bash
#!/bin/bash
# continuous_test.sh

while true; do
  clear
  echo "AUPEX Continuous Testing - $(date)"
  echo "================================"
  
  # Check website
  if curl -s -o /dev/null -w "%{http_code}" http://aupex.ai | grep -q "200"; then
    echo "✅ Website: OK"
  else
    echo "❌ Website: FAILED"
  fi
  
  # Check API
  if curl -s http://aupex.ai/api/health | grep -q "healthy"; then
    echo "✅ API: OK"
  else
    echo "❌ API: FAILED"
  fi
  
  # Check WebSocket
  if curl -s -o /dev/null -w "%{http_code}" \
     -H "Upgrade: websocket" \
     -H "Connection: Upgrade" \
     http://aupex.ai/ws | grep -q "101\|426"; then
    echo "✅ WebSocket: OK"
  else
    echo "❌ WebSocket: FAILED"
  fi
  
  sleep 30
done
```

---

## 📋 Testing Checklist

### Pre-Deployment Testing
- [ ] All pages load without errors
- [ ] Navigation works correctly
- [ ] 3D animations render
- [ ] API endpoints respond
- [ ] WebSocket connects
- [ ] Mobile responsive
- [ ] No console errors

### Post-Deployment Testing
- [ ] DNS resolves correctly
- [ ] SSL certificate valid (when enabled)
- [ ] All resources load from correct domain
- [ ] API calls use correct URLs
- [ ] WebSocket connects to production
- [ ] Performance acceptable
- [ ] No mixed content warnings

### User Acceptance Testing
- [ ] Homepage impressive
- [ ] Agent pages informative
- [ ] Interactions smooth
- [ ] Load time acceptable
- [ ] Mobile experience good
- [ ] No broken links
- [ ] Content accurate

---

## 🐛 Common Issues & Solutions

### Issue: 3D graphics not rendering
```javascript
// Solution: Check WebGL support
if (!window.WebGLRenderingContext) {
  console.error('WebGL not supported');
  // Show fallback content
}
```

### Issue: WebSocket not connecting
```javascript
// Solution: Check connection and retry
let retries = 0;
function connectWebSocket() {
  const ws = new WebSocket('ws://aupex.ai/ws/dashboard/test');
  ws.onerror = () => {
    if (retries++ < 3) {
      setTimeout(connectWebSocket, 1000 * retries);
    }
  };
}
```

### Issue: Slow page load
```bash
# Diagnose: Check what's slow
curl -o /dev/null -s -w "\
DNS: %{time_namelookup}s\n\
Connect: %{time_connect}s\n\
Start Transfer: %{time_starttransfer}s\n\
Total: %{time_total}s\n" http://aupex.ai
```

---

## 🎯 Testing Best Practices

1. **Test early and often**
2. **Document test results**
3. **Test on real devices when possible**
4. **Clear cache between tests**
5. **Test both happy and error paths**
6. **Monitor performance over time**
7. **Get feedback from real users**

---

*Remember: Thorough testing prevents production issues!*

*Last Updated: January 20, 2025* 