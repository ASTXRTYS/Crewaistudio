# AUPEX.AI Website Metric Integration Example

## Quick Start: Add HRV Display to Homepage

### 1. Add to your HTML (where you want the metric):
```html
<div class="metric-display">
    <h3>Your Current HRV</h3>
    <div id="hrv-gauge" class="metric-gauge">
        <span class="metric-value">--</span>
        <span class="metric-unit">ms</span>
    </div>
    <p class="metric-status">Loading...</p>
</div>
```

### 2. Add JavaScript to fetch and display:
```javascript
// Function to update HRV display
async function updateHRV(userId) {
    try {
        // Fetch current HRV value
        const response = await fetch(`http://144.126.215.218:8002/api/metrics/current/auren_hrv_rmssd_ms?user_id=${userId}`);
        const data = await response.json();
        
        // Update display
        document.querySelector('#hrv-gauge .metric-value').textContent = 
            data.value ? Math.round(data.value) : '--';
        
        // Update status based on thresholds
        const status = document.querySelector('.metric-status');
        if (data.value < 20) {
            status.textContent = '⚠️ Critical - Rest recommended';
            status.className = 'metric-status critical';
        } else if (data.value < 30) {
            status.textContent = '⚡ Low - Reduce intensity';
            status.className = 'metric-status warning';
        } else if (data.value > 100) {
            status.textContent = '❓ Check measurement';
            status.className = 'metric-status elevated';
        } else {
            status.textContent = '✅ Optimal';
            status.className = 'metric-status good';
        }
    } catch (error) {
        console.error('Failed to fetch HRV:', error);
    }
}

// Update every 30 seconds
setInterval(() => updateHRV('user123'), 30000);
updateHRV('user123'); // Initial load
```

### 3. Add CSS styling:
```css
.metric-display {
    background: rgba(0, 255, 136, 0.05);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 12px;
    padding: 24px;
    text-align: center;
}

.metric-gauge {
    font-size: 48px;
    font-weight: bold;
    margin: 16px 0;
}

.metric-value {
    color: #00ff88;
}

.metric-unit {
    font-size: 24px;
    opacity: 0.7;
}

.metric-status {
    font-size: 14px;
    margin-top: 12px;
}

.metric-status.good { color: #00ff88; }
.metric-status.warning { color: #ffaa00; }
.metric-status.critical { color: #ff4444; }
.metric-status.elevated { color: #aaaaff; }
```

## For a Full Dashboard Page

You could create a dedicated metrics page on AUPEX.AI:

```javascript
// Fetch all metrics at once
async function loadDashboard(userId) {
    const response = await fetch('http://144.126.215.218:8002/api/metrics/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            metrics: [
                'auren_hrv_rmssd_ms',
                'auren_sleep_debt_hours',
                'auren_recovery_score'
            ],
            user_id: userId,
            time_range: '24h'
        })
    });
    
    const data = await response.json();
    // Update multiple displays...
}
```

## Real-time Updates with WebSocket

For live updates without polling:

```javascript
const ws = new WebSocket('ws://144.126.215.218:8002/api/metrics/stream');

ws.onopen = () => {
    // Subscribe to metrics
    ws.send(JSON.stringify({
        metrics: ['auren_hrv_rmssd_ms', 'auren_recovery_score'],
        user_id: 'user123'
    }));
};

ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    if (update.type === 'metric_update') {
        // Update UI with new value
        console.log(`${update.metric}: ${update.value}`);
    }
};
```

## Which Metrics to Show Where?

### Homepage (AUPEX.AI)
- **Recovery Score** - Big, prominent gauge
- **Current Status** - Good/Warning/Critical indicator

### User Dashboard
- **All three metrics** with trends
- **24-hour charts**
- **Weekly summaries**

### Mobile PWA
- **Simplified view** - Just current values
- **Push notifications** when thresholds exceeded

The beauty is you can start simple (just show current HRV) and gradually add more sophisticated visualizations!