# 🌉 Observability Frontend Bridge - Implementation Guide

**Date**: August 1, 2025  
**Purpose**: Enable selective exposure of backend metrics to front-end  
**Principle**: Build once, expose selectively

---

## 🎯 Executive Summary

This implementation creates a flexible bridge between your complete backend observability (Prometheus/Grafana) and your front-end, allowing you to say:

> "Hey engineer, make the HRV trend visible on the user dashboard"

And they can do it in 30 minutes by adding one API endpoint and one React component.

---

## 🏗️ Architecture Overview

```
Backend Observability (Complete)
├── Prometheus (All Metrics)
├── Grafana (Internal Dashboards)
└── API Bridge (New)
    ├── /api/metrics/query     - Query any metric
    ├── /api/metrics/stream    - WebSocket for real-time
    └── /api/metrics/catalog   - List available metrics

Front-End (Selective)
├── MetricsProvider (React Context)
├── useMetric() Hook
└── <MetricChart /> Component
```

---

## 📦 Phase 1: API Bridge Implementation

### 1.1 Create Metrics API Service

```python
# auren/api/metrics_bridge.py
from fastapi import FastAPI, WebSocket
from prometheus_client.parser import text_string_to_metric_families
import httpx
import asyncio
from typing import Dict, List, Optional

app = FastAPI()

PROMETHEUS_URL = "http://localhost:9090"

@app.get("/api/metrics/catalog")
async def get_available_metrics():
    """List all available metrics from KPI registry"""
    # Read from kpi_registry.yaml
    with open("agents/shared_modules/kpi_registry.yaml") as f:
        registry = yaml.safe_load(f)
    
    return {
        "metrics": [
            {
                "id": kpi["name"],
                "name": kpi["description"],
                "metric": kpi["prometheus_metric"],
                "unit": kpi["unit"],
                "category": kpi.get("category", "general")
            }
            for kpi in registry["kpis"]
        ]
    }

@app.get("/api/metrics/query/{metric_name}")
async def query_metric(
    metric_name: str,
    user_id: Optional[str] = None,
    time_range: str = "1h"
):
    """Query specific metric from Prometheus"""
    query = f'{metric_name}'
    if user_id:
        query += f'{{user_id="{user_id}"}}'
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params={
                "query": query,
                "start": f"now-{time_range}",
                "end": "now",
                "step": "15s"
            }
        )
    
    data = response.json()
    
    # Transform Prometheus format to frontend-friendly format
    if data["status"] == "success" and data["data"]["result"]:
        result = data["data"]["result"][0]
        return {
            "metric": metric_name,
            "data": [
                {
                    "timestamp": int(ts),
                    "value": float(val)
                }
                for ts, val in result["values"]
            ]
        }
    
    return {"metric": metric_name, "data": []}

@app.websocket("/api/metrics/stream")
async def metrics_stream(websocket: WebSocket):
    """Real-time metric streaming"""
    await websocket.accept()
    
    try:
        while True:
            # Client sends: {"metrics": ["auren_hrv_rmssd_ms"], "user_id": "123"}
            request = await websocket.receive_json()
            
            # Query current values
            for metric in request.get("metrics", []):
                value = await get_current_metric_value(
                    metric, 
                    request.get("user_id")
                )
                
                await websocket.send_json({
                    "metric": metric,
                    "value": value,
                    "timestamp": int(time.time())
                })
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except Exception:
        await websocket.close()
```

### 1.2 Add to Docker Compose

```yaml
# docker-compose.production.override.yml
services:
  metrics-bridge:
    image: auren/metrics-bridge:latest
    container_name: auren-metrics-bridge
    networks:
      - auren-network
    ports:
      - "8002:8002"
    environment:
      - PROMETHEUS_URL=http://auren-prometheus:9090
    restart: unless-stopped
```

---

## 🎨 Phase 2: Front-End Integration

### 2.1 React Metrics Provider

```javascript
// src/contexts/MetricsProvider.jsx
import React, { createContext, useContext, useEffect, useState } from 'react';

const MetricsContext = createContext();

export const MetricsProvider = ({ children }) => {
  const [catalog, setCatalog] = useState([]);
  const [ws, setWs] = useState(null);
  const [realTimeData, setRealTimeData] = useState({});

  useEffect(() => {
    // Fetch metric catalog on mount
    fetch('/api/metrics/catalog')
      .then(res => res.json())
      .then(data => setCatalog(data.metrics));

    // Setup WebSocket for real-time data
    const websocket = new WebSocket('ws://144.126.215.218:8002/api/metrics/stream');
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setRealTimeData(prev => ({
        ...prev,
        [data.metric]: data
      }));
    };
    setWs(websocket);

    return () => websocket.close();
  }, []);

  const queryMetric = async (metricName, options = {}) => {
    const params = new URLSearchParams(options);
    const response = await fetch(`/api/metrics/query/${metricName}?${params}`);
    return response.json();
  };

  const subscribeToMetric = (metricName, userId) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        metrics: [metricName],
        user_id: userId
      }));
    }
  };

  return (
    <MetricsContext.Provider value={{
      catalog,
      queryMetric,
      subscribeToMetric,
      realTimeData
    }}>
      {children}
    </MetricsContext.Provider>
  );
};

export const useMetrics = () => useContext(MetricsContext);
```

### 2.2 Reusable Metric Component

```javascript
// src/components/MetricChart.jsx
import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import { useMetrics } from '../contexts/MetricsProvider';

export const MetricChart = ({ 
  metricName, 
  userId, 
  title, 
  realTime = false,
  timeRange = '1h' 
}) => {
  const { queryMetric, subscribeToMetric, realTimeData } = useMetrics();
  const [chartData, setChartData] = useState({ labels: [], datasets: [] });

  useEffect(() => {
    // Initial data load
    queryMetric(metricName, { user_id: userId, time_range: timeRange })
      .then(data => {
        setChartData({
          labels: data.data.map(d => new Date(d.timestamp * 1000).toLocaleTimeString()),
          datasets: [{
            label: title || metricName,
            data: data.data.map(d => d.value),
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
          }]
        });
      });

    // Subscribe to real-time updates if enabled
    if (realTime) {
      subscribeToMetric(metricName, userId);
    }
  }, [metricName, userId, timeRange]);

  // Update chart with real-time data
  useEffect(() => {
    if (realTime && realTimeData[metricName]) {
      const newData = realTimeData[metricName];
      setChartData(prev => ({
        labels: [...prev.labels.slice(-59), new Date(newData.timestamp * 1000).toLocaleTimeString()],
        datasets: [{
          ...prev.datasets[0],
          data: [...prev.datasets[0].data.slice(-59), newData.value]
        }]
      }));
    }
  }, [realTimeData, metricName]);

  return (
    <div className="metric-chart">
      <Line data={chartData} options={{
        responsive: true,
        plugins: {
          legend: { position: 'top' },
          title: { display: true, text: title }
        }
      }} />
    </div>
  );
};
```

### 2.3 Usage Example - Adding HRV to User Dashboard

```javascript
// src/pages/UserDashboard.jsx
import { MetricChart } from '../components/MetricChart';

export const UserDashboard = ({ userId }) => {
  return (
    <div className="dashboard">
      <h1>Your Neural Optimization Dashboard</h1>
      
      {/* Engineer adds this one line to show HRV */}
      <MetricChart 
        metricName="auren_hrv_rmssd_ms"
        userId={userId}
        title="Heart Rate Variability"
        realTime={true}
        timeRange="24h"
      />
      
      {/* Add more metrics as needed */}
      <MetricChart 
        metricName="auren_sleep_debt_hours"
        userId={userId}
        title="Sleep Debt Trend"
        timeRange="7d"
      />
    </div>
  );
};
```

---

## 🚀 Phase 3: Making It Even Easier

### 3.1 Metric Gallery Component

```javascript
// src/components/MetricGallery.jsx
export const MetricGallery = () => {
  const { catalog } = useMetrics();
  const [selectedMetrics, setSelectedMetrics] = useState([]);

  return (
    <div className="metric-gallery">
      <h2>Available Metrics</h2>
      <div className="metric-grid">
        {catalog.map(metric => (
          <div key={metric.id} className="metric-card">
            <h3>{metric.name}</h3>
            <p>Category: {metric.category}</p>
            <p>Unit: {metric.unit}</p>
            <button onClick={() => {
              navigator.clipboard.writeText(
                `<MetricChart metricName="${metric.metric}" userId={userId} title="${metric.name}" />`
              );
              alert('Component code copied to clipboard!');
            }}>
              Copy Component Code
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 3.2 No-Code Metric Builder

```python
# scripts/add_frontend_metric.py
#!/usr/bin/env python3
"""
Usage: ./add_frontend_metric.py --metric auren_hrv_rmssd_ms --page user-dashboard
"""

import argparse
import re

def add_metric_to_page(metric_name, page_name, title=None):
    # Read page component
    page_file = f"src/pages/{page_name}.jsx"
    with open(page_file, 'r') as f:
        content = f.read()
    
    # Find where to insert
    insert_point = content.find('{/* METRICS_INSERT_POINT */}')
    
    # Generate component
    component = f'''
      <MetricChart 
        metricName="{metric_name}"
        userId={{userId}}
        title="{title or metric_name}"
        realTime={{true}}
      />
      {{/* METRICS_INSERT_POINT */}}'''
    
    # Insert
    new_content = content[:insert_point] + component + content[insert_point:]
    
    # Write back
    with open(page_file, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Added {metric_name} to {page_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metric", required=True)
    parser.add_argument("--page", required=True)
    parser.add_argument("--title", default=None)
    args = parser.parse_args()
    
    add_metric_to_page(args.metric, args.page, args.title)
```

---

## 🎯 The Result

With this setup, when you tell an engineer "Make the cognitive load metric visible on the athlete dashboard", they can:

1. **Option A**: Add one line of JSX
   ```jsx
   <MetricChart metricName="auren_cognitive_load_percent" userId={userId} title="Cognitive Load" />
   ```

2. **Option B**: Run a script
   ```bash
   ./add_frontend_metric.py --metric auren_cognitive_load_percent --page athlete-dashboard
   ```

3. **Option C**: Use the visual builder in development mode

---

## 📊 What You Get

1. **Complete backend observability** remains intact
2. **Selective front-end exposure** on demand
3. **Real-time updates** via WebSocket
4. **Historical data** via REST API
5. **No duplication** - single source of truth
6. **30-minute implementation** for new metrics

---

## 🔒 Security Considerations

1. **API Gateway** filters which metrics are exposed
2. **User-scoped queries** prevent data leakage
3. **Rate limiting** on API endpoints
4. **Authentication** via existing auth system

---

## 🚀 Next Steps

1. Implement the metrics bridge API
2. Add the React components to your PWA
3. Create a few example metrics on the front-end
4. Document the process for other engineers

This gives you exactly what you want: the ability to cherry-pick backend metrics for front-end display without rebuilding anything!