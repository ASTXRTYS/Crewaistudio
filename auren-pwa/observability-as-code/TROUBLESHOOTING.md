# 🔧 Observability Troubleshooting Guide

**Common issues and how to fix them**

---

## 🚨 Quick Diagnostics

Run this first to check system health:

```bash
# Check all services are running
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

# Test metrics API
curl -s http://144.126.215.218:8002/health | jq

# Check NEUROS metrics endpoint
curl -s http://144.126.215.218:8000/metrics | grep -c "auren_"

# Test Prometheus
curl -s http://144.126.215.218:9090/api/v1/targets | jq '.data.activeTargets[].health'
```

---

## 📋 Common Issues

### <a name="kpi-not-showing"></a>1. "I added a KPI but it's not showing up"

**Symptoms**: Added to YAML, but metric returns no data

**Check these in order**:

1. **Validate YAML syntax**:
```bash
python3 scripts/validate_kpi_registry.py
```

2. **Regenerate and deploy configs**:
```bash
# Regenerate
python3 scripts/generate_dashboards.py --input agents/shared_modules/kpi_registry.yaml --output grafana/dashboards/kpi-generated.json
python3 scripts/generate_recording_rules.py --input agents/shared_modules/kpi_registry.yaml --output prometheus/rules/kpi-generated.yml

# Deploy
sshpass -p '.HvddX+@6dArsKd' scp prometheus/rules/kpi-generated.yml root@144.126.215.218:/opt/prometheus/rules/
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'curl -X POST localhost:9090/-/reload'
```

3. **Check if agent is emitting the metric**:
```bash
# Check NEUROS metrics endpoint
curl -s http://144.126.215.218:8000/metrics | grep "your_metric_name"
```

4. **Restart the agent** (metrics are loaded at startup):
```bash
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker restart neuros-advanced'
```

5. **Check Prometheus is scraping**:
```bash
# Check targets
curl -s http://144.126.215.218:9090/targets | grep neuros

# Query Prometheus directly
curl -s "http://144.126.215.218:9090/api/v1/query?query=your_metric_name" | jq
```

---

### <a name="no-data"></a>2. "Metric shows '--' on frontend"

**Symptoms**: API returns null or no data

**Solutions**:

1. **Check metric exists in catalog**:
```bash
curl -s http://144.126.215.218:8002/api/metrics/catalog | jq '.metrics[].metric'
```

2. **Test the metric directly**:
```bash
# Without user_id
curl -s "http://144.126.215.218:8002/api/metrics/current/auren_hrv_rmssd_ms"

# With user_id
curl -s "http://144.126.215.218:8002/api/metrics/current/auren_hrv_rmssd_ms?user_id=demo"
```

3. **Check CORS if from browser**:
```javascript
// Add to your fetch
fetch(url, {
    mode: 'cors',
    headers: {
        'Content-Type': 'application/json'
    }
})
```

4. **Check WebSocket connection**:
```javascript
// In browser console
const ws = new WebSocket('ws://144.126.215.218:8002/api/metrics/stream');
ws.onopen = () => console.log('Connected');
ws.onerror = (e) => console.error('WebSocket error:', e);
```

---

### 3. "Container keeps restarting"

**Symptoms**: `docker ps` shows "Restarting" status

**Solutions**:

1. **Check logs**:
```bash
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker logs --tail 50 container_name'
```

2. **Common fixes**:

**NEUROS**:
```bash
# Missing KPI registry
sshpass -p '.HvddX+@6dArsKd' scp agents/shared_modules/kpi_registry.yaml root@144.126.215.218:/opt/neuros/shared_modules/
```

**Metrics Bridge**:
```bash
# Port conflict
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'lsof -i :8002'
```

**OTel Collector**:
```bash
# Config syntax error
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'cat /opt/otel/otel-collector-simple.yaml | head -20'
```

---

### 4. "Grafana dashboard is empty"

**Symptoms**: Dashboard exists but no data

**Solutions**:

1. **Check datasource**:
```bash
# Should return "success"
curl -s http://144.126.215.218:3000/api/datasources/proxy/1/api/v1/query?query=up | jq '.status'
```

2. **Verify dashboard was deployed**:
```bash
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'ls -la /opt/grafana/dashboards/'
```

3. **Force dashboard reload**:
```bash
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker restart auren-grafana'
```

---

### 5. "Alerts not firing"

**Symptoms**: Threshold exceeded but no alerts

**Solutions**:

1. **Check alert rules loaded**:
```bash
curl -s http://144.126.215.218:9090/api/v1/rules | jq '.data.groups[].name'
```

2. **Check alert state**:
```bash
curl -s http://144.126.215.218:9090/api/v1/alerts | jq
```

3. **Verify thresholds**:
```bash
# Check current value vs threshold
curl -s "http://144.126.215.218:9090/api/v1/query?query=auren_hrv_rmssd_ms" | jq '.data.result[0].value[1]'
```

---

### 6. "WebSocket disconnects frequently"

**Symptoms**: Real-time updates stop working

**Solutions**:

1. **Add reconnection logic**:
```javascript
let ws;
let reconnectInterval;

function connect() {
    ws = new WebSocket('ws://144.126.215.218:8002/api/metrics/stream');
    
    ws.onopen = () => {
        console.log('Connected');
        clearInterval(reconnectInterval);
    };
    
    ws.onclose = () => {
        console.log('Disconnected, reconnecting...');
        reconnectInterval = setInterval(connect, 5000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
    };
}

connect();
```

2. **Check network**:
```bash
# From your machine
ping 144.126.215.218
traceroute 144.126.215.218
```

---

### 7. "Agent-specific KPIs not working"

**Symptoms**: Shared KPIs work but agent-specific don't

**Current Limitation**: Only NEUROS has a complete implementation. For other agents:

1. **Create agent YAML profile first**:
```yaml
# agents/nutros_modules/kpi_bindings.yaml
kpis:
  - name: "glucose_variability"
    prometheus_metric: "auren_glucose_cv"
```

2. **Update agent code to use kpi_emitter**:
```python
# In agent implementation
from shared_modules.kpi_emitter import emit
emit("glucose_variability", calculated_value)
```

3. **Deploy new agent container** with KPI support

---

## 🔍 Debug Commands

### Check Everything
```bash
# One command to check all
curl -s http://144.126.215.218:8002/api/metrics/catalog | jq '.metrics | length' && \
echo "Metrics Bridge: ✅" || echo "Metrics Bridge: ❌"

curl -s http://144.126.215.218:8000/health | grep -q healthy && \
echo "NEUROS: ✅" || echo "NEUROS: ❌"

curl -s http://144.126.215.218:9090/-/healthy | grep -q "Prometheus is Healthy" && \
echo "Prometheus: ✅" || echo "Prometheus: ❌"

curl -s http://144.126.215.218:3000/api/health | grep -q ok && \
echo "Grafana: ✅" || echo "Grafana: ❌"
```

### Container Logs
```bash
# All logs at once
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 '
for container in neuros-advanced auren-metrics-bridge auren-prometheus auren-grafana; do
    echo "=== $container ==="
    docker logs --tail 10 $container 2>&1
    echo
done
'
```

### Metric Flow Test
```bash
# Test complete flow
echo "1. Check KPI Registry..."
grep "auren_hrv_rmssd_ms" agents/shared_modules/kpi_registry.yaml && echo "✅ Found in registry"

echo "2. Check NEUROS emission..."
curl -s http://144.126.215.218:8000/metrics | grep -q "auren_hrv_rmssd_ms" && echo "✅ Emitted by NEUROS"

echo "3. Check Prometheus..."
curl -s "http://144.126.215.218:9090/api/v1/query?query=auren_hrv_rmssd_ms" | jq -e '.data.result[0]' > /dev/null && echo "✅ In Prometheus"

echo "4. Check Metrics Bridge..."
curl -s http://144.126.215.218:8002/api/metrics/current/auren_hrv_rmssd_ms | jq -e '.value' > /dev/null && echo "✅ Available via API"
```

---

## 💡 Prevention Tips

1. **Always validate YAML** before deploying
2. **Test locally** with a subset of data first
3. **Monitor disk space** - Prometheus can fill up fast
4. **Set up alerts** for the monitoring system itself
5. **Document any manual changes** immediately

---

## 🆘 Still Stuck?

1. Check container resource usage:
```bash
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker stats --no-stream'
```

2. Check disk space:
```bash
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'df -h'
```

3. Review the architecture diagram in [README.md](./README.md)

4. Check if similar issue in handoff docs:
   - `OTEL_COLLECTOR_HANDOFF_DOCUMENT.md`
   - `OBSERVABILITY_AS_CODE_HANDOFF.md`

---

*Remember: Most issues are either configuration syntax or services not restarted after changes.*