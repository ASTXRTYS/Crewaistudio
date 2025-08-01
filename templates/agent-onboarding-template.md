# 🚀 AUREN Agent Onboarding Template

*Copy this template for each new agent (NUTROS, KINETOS, HYPERTROS, etc.)*

## Agent Configuration

```bash
# === STEP 1: AGENT DETAILS (30 seconds) ===
AGENT_NAME="[AGENT_NAME_LOWERCASE]"    # e.g., nutros, kinetos, hypertros
AGENT_PORT="[UNIQUE_PORT]"             # e.g., 8012, 8013, 8014
METRICS_PATH="/metrics"                # Standard for all agents
TRACES_ENABLED="true"                  # Enable OpenTelemetry traces
```

## Implementation Checklist

### ✅ **Phase 1: Code Integration (5 minutes)**
```python
# 1. Add to requirements.txt
prometheus-fastapi-instrumentator==1.1.1
opentelemetry-distro==0.45b0
opentelemetry-exporter-prometheus==0.45b0
opentelemetry-instrumentation-fastapi==0.45b0

# 2. Add to main.py (2 lines)
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# 3. Declare KPI metrics
from prometheus_client import Gauge, Counter

# Replace [AGENT] with actual agent name
HRV = Gauge("[AGENT]_hrv_rmssd_ms", "HRV RMSSD in milliseconds", ['user_id', 'agent'])
SLEEP_DEBT = Gauge("[AGENT]_sleep_debt_hours", "Sleep debt in hours", ['user_id', 'agent'])
RECOVERY = Gauge("[AGENT]_recovery_score", "Recovery score 0-100", ['user_id', 'agent'])

# Risk counters
HRV_RISK = Counter("[AGENT]_hrv_risk_total", "HRV risk events", ['user_id', 'agent', 'severity'])
SLEEP_RISK = Counter("[AGENT]_sleep_risk_total", "Sleep risk events", ['user_id', 'agent', 'severity'])
RECOVERY_RISK = Counter("[AGENT]_recovery_risk_total", "Recovery risk events", ['user_id', 'agent', 'severity'])

# 4. Environment guard (optional)
import os
if os.getenv("OTEL_ENABLED", "false").lower() == "true":
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor().instrument_app(app)
```

### ✅ **Phase 2: Infrastructure (5 minutes)**
```bash
# 1. Add Prometheus scrape target
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 '
echo "
  - job_name: \"${AGENT_NAME}-prod\"
    metrics_path: ${METRICS_PATH}
    static_configs:
      - targets: [\"${AGENT_NAME}-container:${AGENT_PORT}\"]
" >> /opt/prometheus.yml'

# 2. Reload Prometheus (zero downtime)
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 '
curl -X POST http://localhost:9090/-/reload || docker restart auren-prometheus'
```

### ✅ **Phase 3: Dashboard Setup (5 minutes)**
```bash
# 1. Copy dashboard template
cp grafana/dashboards/auren-kpi-overview-dashboard.json grafana/dashboards/auren-kpi-[AGENT]-dashboard.json

# 2. Replace all instances of "neuros" with "[AGENT]" in the new file
sed -i 's/neuros/[AGENT]/g' grafana/dashboards/auren-kpi-[AGENT]-dashboard.json
sed -i 's/NEUROS/[AGENT_UPPERCASE]/g' grafana/dashboards/auren-kpi-[AGENT]-dashboard.json

# 3. Update dashboard title and UID
sed -i 's/"title": "AUREN KPI Overview - NEUROS Agent"/"title": "AUREN KPI Overview - [AGENT_UPPERCASE] Agent"/g' grafana/dashboards/auren-kpi-[AGENT]-dashboard.json
sed -i 's/"uid": "auren-kpi-neuros"/"uid": "auren-kpi-[AGENT]"/g' grafana/dashboards/auren-kpi-[AGENT]-dashboard.json
```

## Verification Tests

### 🔍 **Test 1: Metrics Endpoint (2 minutes)**
```bash
# Inside agent container
curl -s http://localhost:${AGENT_PORT}/metrics | head -20
# Look for: [AGENT]_hrv_rmssd_ms, [AGENT]_sleep_debt_hours, [AGENT]_recovery_score

# From Prometheus server
curl -s http://localhost:9090/api/v1/query?query=${AGENT_NAME}_hrv_rmssd_ms
```

### 🔍 **Test 2: Prometheus Scraping (1 minute)**
```bash
# Check target status
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="'${AGENT_NAME}'-prod")'
```

### 🔍 **Test 3: Grafana Visualization (2 minutes)**
```bash
# Access Grafana: http://144.126.215.218:3000
# Navigate to: Dashboards > AUREN > [AGENT] KPI Overview
# Verify: All panels show data
```

## Success Criteria

✅ **Metrics visible**: `curl http://localhost:${AGENT_PORT}/metrics` shows agent KPIs  
✅ **Prometheus scraping**: Target shows UP status  
✅ **Grafana dashboard**: All panels display data  
✅ **Zero errors**: No container restart loops  
✅ **CI passing**: All validation gates pass  

## Troubleshooting

### ❌ **Container restart loop**
```bash
# Check logs
docker logs ${AGENT_NAME}-container --tail=50

# Common fixes
pip install opentelemetry-instrumentation-fastapi==0.45b0
```

### ❌ **Metrics not appearing**
```bash
# Verify Instrumentator setup
grep -r "Instrumentator" /path/to/agent/code

# Check port mapping
docker ps | grep ${AGENT_NAME}
```

### ❌ **Prometheus not scraping**
```bash
# Check target configuration
docker exec auren-prometheus cat /etc/prometheus/prometheus.yml | grep -A 5 ${AGENT_NAME}

# Reload configuration
curl -X POST http://localhost:9090/-/reload
```

---

## 📊 **Expected Timeline**

| Phase | Duration | Task |
|-------|----------|------|
| **Setup** | 30 seconds | Configure agent variables |
| **Code** | 5 minutes | Add instrumentator + KPI declarations |
| **Infrastructure** | 5 minutes | Prometheus + dashboard setup |
| **Testing** | 5 minutes | End-to-end verification |
| **Total** | **≈15 minutes** | **Complete observability onboarding** |

---

**🎯 Success**: Agent KPIs visible in Grafana with real-time updates, alerts configured, enterprise-grade observability complete!