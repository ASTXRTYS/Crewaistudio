# ⚡ Observability Quick Start Guide

**Get a metric from YAML to front-end in 5 minutes**

---

## 🎯 For Engineers in a Hurry

### Scenario 1: "Add this metric to the website"

**Request**: "Show real-time stress levels on the dashboard"

**Steps**:

1. **Check if metric exists**:
```bash
curl http://144.126.215.218:8002/api/metrics/catalog | jq
```

2. **If it exists**, add to your page:
```javascript
// Add to HTML
<div id="stress-level">--</div>

// Add to JavaScript
async function updateStressLevel() {
    const res = await fetch('http://144.126.215.218:8002/api/metrics/current/auren_stress_level?user_id=demo');
    const data = await res.json();
    document.getElementById('stress-level').textContent = data.value || '--';
}
setInterval(updateStressLevel, 30000);
updateStressLevel();
```

3. **If it doesn't exist**, see Scenario 2.

---

### Scenario 2: "Create a new metric"

**Request**: "Track attention span duration"

**Steps**:

1. **Add to KPI Registry**:
```bash
# Edit: agents/shared_modules/kpi_registry.yaml
# Add:
- name: "attention_span"
  description: "Current attention span duration"
  unit: "minutes"
  prometheus_metric: "auren_attention_span_minutes"
  category: "cognitive"
```

2. **Generate configs**:
```bash
cd /path/to/CrewAI-Studio-main

# Generate everything
python3 scripts/generate_dashboards.py \
  --input agents/shared_modules/kpi_registry.yaml \
  --output grafana/dashboards/kpi-generated.json

python3 scripts/generate_recording_rules.py \
  --input agents/shared_modules/kpi_registry.yaml \
  --output prometheus/rules/kpi-generated.yml

python3 scripts/generate_alerts.py \
  --input agents/shared_modules/kpi_registry.yaml \
  --output prometheus/alerts/kpi-generated.yml
```

3. **Deploy**:
```bash
# Copy to server
sshpass -p '.HvddX+@6dArsKd' scp prometheus/rules/kpi-generated.yml root@144.126.215.218:/opt/prometheus/rules/
sshpass -p '.HvddX+@6dArsKd' scp prometheus/alerts/kpi-generated.yml root@144.126.215.218:/opt/prometheus/alerts/
sshpass -p '.HvddX+@6dArsKd' scp grafana/dashboards/kpi-generated.json root@144.126.215.218:/opt/grafana/dashboards/

# Reload services
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'curl -X POST localhost:9090/-/reload'
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker restart auren-grafana'
```

4. **Update agent to emit metric** (if needed):
```python
# In agent code
from shared_modules.kpi_emitter import emit
emit("attention_span", calculated_attention_span)
```

5. **Use on front-end** (same as Scenario 1)

---

## 🔥 Copy-Paste Examples

### React Component
```jsx
import { useEffect, useState } from 'react';

function MetricDisplay({ metricName, userId = 'demo' }) {
    const [value, setValue] = useState('--');
    const [status, setStatus] = useState('');
    
    useEffect(() => {
        async function fetchMetric() {
            try {
                const res = await fetch(
                    `http://144.126.215.218:8002/api/metrics/current/${metricName}?user_id=${userId}`
                );
                const data = await res.json();
                setValue(data.value ? data.value.toFixed(1) : '--');
            } catch (err) {
                console.error(err);
            }
        }
        
        fetchMetric();
        const interval = setInterval(fetchMetric, 30000);
        return () => clearInterval(interval);
    }, [metricName, userId]);
    
    return (
        <div className="metric">
            <h3>{metricName}</h3>
            <div className="value">{value}</div>
        </div>
    );
}

// Usage
<MetricDisplay metricName="auren_hrv_rmssd_ms" />
```

### Vanilla JavaScript
```javascript
class MetricDisplay {
    constructor(elementId, metricName, userId = 'demo') {
        this.element = document.getElementById(elementId);
        this.metricName = metricName;
        this.userId = userId;
        this.update();
        setInterval(() => this.update(), 30000);
    }
    
    async update() {
        try {
            const res = await fetch(
                `http://144.126.215.218:8002/api/metrics/current/${this.metricName}?user_id=${this.userId}`
            );
            const data = await res.json();
            this.element.textContent = data.value ? data.value.toFixed(1) : '--';
        } catch (err) {
            this.element.textContent = 'Error';
        }
    }
}

// Usage
new MetricDisplay('hrv-display', 'auren_hrv_rmssd_ms');
```

### WebSocket Real-time
```javascript
const ws = new WebSocket('ws://144.126.215.218:8002/api/metrics/stream');

ws.onopen = () => {
    ws.send(JSON.stringify({
        metrics: ['auren_hrv_rmssd_ms', 'auren_recovery_score'],
        user_id: 'demo'
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'metric_update') {
        document.getElementById(data.metric).textContent = data.value;
    }
};
```

---

## 📋 Cheat Sheet

### API Endpoints
```bash
# List all metrics
GET http://144.126.215.218:8002/api/metrics/catalog

# Get current value
GET http://144.126.215.218:8002/api/metrics/current/{metric_name}?user_id={user_id}

# Get historical data
GET http://144.126.215.218:8002/api/metrics/query/{metric_name}?user_id={user_id}&time_range=1h

# Get aggregates (min/max/avg)
GET http://144.126.215.218:8002/api/metrics/aggregates?metric_name={metric_name}&user_id={user_id}

# Batch request
POST http://144.126.215.218:8002/api/metrics/batch
Body: {
    "metrics": ["auren_hrv_rmssd_ms", "auren_recovery_score"],
    "user_id": "demo",
    "time_range": "1h"
}

# WebSocket
ws://144.126.215.218:8002/api/metrics/stream
```

### Current Metrics
- `auren_hrv_rmssd_ms` - Heart Rate Variability (ms)
- `auren_recovery_score` - Recovery Score (0-100)
- `auren_sleep_debt_hours` - Sleep Debt (hours)

### File Locations
- KPI Registry: `agents/shared_modules/kpi_registry.yaml`
- Generator Scripts: `scripts/generate_*.py`
- Server Configs: `/opt/prometheus/`, `/opt/grafana/`

---

## 🚀 That's It!

You now know how to:
1. ✅ Check available metrics
2. ✅ Add new metrics
3. ✅ Display on front-end
4. ✅ Get real-time updates

For more details, see the [full documentation](./README.md).