# Enterprise Observability Onboarding (15-Minute Agent Recipe)
## 🎯 **Zero-Touch KPI System for All 9 AUREN Agents**

*Version: 2.0 Enterprise*  
*Compatible with: NEUROS, NUTROS, KINETOS, HYPERTROS, CARDIOS, SOMNOS, OPTICOS, ENDOS, AUREN*  
*Deployment time: 15 minutes per agent*  

---

## 📋 **One-Time Configuration Confirmation**

✅ **Current AUREN Standards** (verified production):

| Configuration | AUREN Default | Status |
|---------------|---------------|--------|
| **Metrics path** | `/metrics` | ✅ Verified |
| **Base port** | 8001 (neuros-blue) | ✅ Production |
| **Python base** | `python:3.11-slim` | ✅ Compatible |
| **Environment flag** | `OTEL_ENABLED=true` | ✅ Configured |

*These defaults work for all 9 agents. Edit once if different, commit, and all future agents inherit the fix.*

---

# Quick-Attach Recipe (Per Agent: ~15 min)

## 1 Install aligned libraries
```bash
pip install prometheus-fastapi-instrumentator==1.1.1 \
            opentelemetry-distro==0.45b0 \
            opentelemetry-exporter-prometheus==0.45b0 \
            opentelemetry-instrumentation-fastapi==0.45b0  # ➝ fixes SDK mismatch
```

## 2 Two-line bootstrap in `main.py`
```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

## 3 Declare KPI metrics
```python
from prometheus_client import Gauge, Counter
HRV_MS = Gauge("neuros_hrv_rmssd_ms", "HRV (RMSSD, ms)")
RISK_CT = Counter("neuros_hrv_risk_total", "HRV risk events")
```

## 4 (Opt.) Guard traces behind an env flag
```python
import os
if os.getenv("OTEL_ENABLED", "false").lower() == "true":
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor().instrument_app(app)
```

## 5 Add Prometheus scrape job
```yaml
- job_name: "neuros-prod"
  metrics_path: /metrics
  static_configs:
    - targets: ["neuros-blue:8001"]
```

## 6 Grafana "KPI Overview" dashboard
* One **Stat + Sparkline** panel per KPI.  
* Thresholds pulled from `shared_modules/kpi_registry.yaml`.  
* Follow Grafana dashboard design guide (consistent units, logical rows).

## 7 Alerts
```yaml
expr: neuros_hrv_rmssd_ms < 25
for: 5m
labels: {severity: "warning"}
```

## 8 Nightly disk & cache hygiene (host cron)
```bash
0 3 * * * docker image prune -a --filter "until=720h" -f
15 3 * * * docker builder prune --all --filter "until=168h" -f
```

## 9 CI gate
pip check + Trivy scan – fail on CVE or version mismatch.
yamllint + Pydantic validator for every YAML change (KPI registry).

---

## 2 "Top-0.1 %" enhancements teams add

| Technique | Why experts do it | References |
|-----------|------------------|------------|
| **Remote BuildKit with `--push`** | Off-host builds stream only the slim runtime layer, preventing overlay2 bloat on prod. | Docker BuildKit |
| **Multi-stage Dockerfile (`COPY . /app` in runtime)** | Guarantees helper modules (e.g., `otel_conditional.py`) land inside the final image, slashing size 40-70 %. | Docker best practices |
| **Memory-limiter processor in Collector** | Caps RAM at ≈ 180 Mi; `otelcol_processor_refused_spans` alerts when pressure hits. | OpenTelemetry |
| **Blue-green via Compose override** | Two-file deployment avoids hand-editing prod YAML; instant rollback. | Docker Compose |
| **Grafana folder & naming conventions** | Prevents dashboard sprawl; keeps units consistent. | Grafana best practices |
| **Cron-prune jobs** | Keeps disk usage < 80 % automatically. | System maintenance |
| **Tempo single-binary in staging** | Get distributed traces with one container; promote when RAM < 200 Mi. | Grafana Tempo |
| **Awesome-Prometheus-Alerts import** | Reuse battle-tested alert rules (service-down, latency, disk). | Prometheus community |

---

## 3 Configuration items to confirm once

| What to confirm | Why it matters |
|-----------------|----------------|
| **Port each agent will expose /metrics** (e.g., HYPERTROS at 8012) | Needed for the Prometheus `static_configs` block. |
| **Same Python 3.11-slim base?** | Ensures the library version pins above work; other bases may need extra packages (libc, ca-certs). |
| **Environment variable strategy** (`OTEL_ENABLED`, secrets) | Guards traces without code edits and keeps API keys out of images. |
| **Grafana folder structure** (`AUREN / KPI Overview`, per-agent sub-folders?) | One decision today prevents future dashboard chaos. |
| **Alert routing (Slack, OpsGenie, e-mail)** | Prometheus alerts must page the right people when HRV risk counters spike. |

If any of those differ in your stack, adjust the doc once and every future agent inherits the fix.

---

## 🚨 **Troubleshooting: Our Hard-Earned Lessons**

### Container Restart Loops (Exit Code 1)
**Root Cause**: Missing dependencies or import errors
```bash
# 1. Check logs first
docker logs CONTAINER_NAME --tail=50

# 2. Common symptoms & fixes:
# "ModuleNotFoundError: langgraph" → Add langgraph to requirements.txt
# "ModuleNotFoundError: opentelemetry.instrumentation.fastapi" → Add opentelemetry-instrumentation-fastapi==0.45b0
# "Import error: prometheus_fastapi_instrumentator" → Add prometheus-fastapi-instrumentator==1.1.1

# 3. Quick verification after fix:
curl http://localhost:PORT/health
# Should return: "metrics_enabled": true
```

### Version Conflict Resolution
**Problem**: Mixed OpenTelemetry SDK versions cause import failures
**Solution**: Use the exact trio that we validated:
```bash
opentelemetry-distro==0.45b0
opentelemetry-exporter-prometheus==0.45b0  
opentelemetry-instrumentation-fastapi==0.45b0
```

### Blue-Green Deployment Safety
**Always keep production stable during debugging**:
```bash
# 1. Stop failing container first
docker stop neuros-blue

# 2. Start known-good fallback
docker start neuros-advanced  

# 3. Fix issues offline, then redeploy
docker restart neuros-blue
```

### Environment Variable Guards
**Critical**: Always guard OpenTelemetry imports to prevent startup crashes:
```python
import os
if os.getenv("OTEL_ENABLED", "false").lower() == "true":
    # OTel imports here - won't crash if missing
    pass
```

---

## 📋 **Implementation Timeline**

| Minute | Task | Expected Outcome |
|--------|------|------------------|
| **0-3** | Install aligned libraries (with versions) | Dependencies resolved, no conflicts |
| **3-8** | Add 2-line instrumentator + KPI gauges | `/metrics` endpoint + custom metrics |
| **8-12** | Update prometheus.yml + environment guards | Scraping configured safely |
| **12-15** | Test & verify all endpoints | End-to-end working |

**Total Time**: ~15 minutes for experienced engineers  
**First Time**: ~25 minutes including documentation reading

---

## 🎯 **Success Checklist**

After implementation, verify:
- [ ] `/health` returns `"metrics_enabled": true`
- [ ] `/metrics` shows your custom gauges
- [ ] `/kpi/demo` generates test data  
- [ ] Prometheus shows service in targets
- [ ] Grafana can query your metrics
- [ ] Container survives restart (no exit code 1 loops)
- [ ] Environment variable guards work (`OTEL_ENABLED=false`)

---

## 🚀 **Next Agent Implementation**

Use this for **NUTROS**, **KINETOS**, **HYPERTROS**, etc.:

1. Copy the requirements.txt template with exact versions
2. Replace `AGENT_NAME` with your agent name  
3. Add agent-specific KPI gauges
4. Follow the 15-minute checklist
5. **No more debugging dependency issues**

### Quick Copy-Paste Template:
```python
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge, Counter
import os

app = FastAPI(title="AGENT_NAME Service")
Instrumentator().instrument(app).expose(app)

# Standard KPI gauges for all agents
HRV_GAUGE = Gauge("AGENT_hrv_rmssd_ms", "Heart Rate Variability", ['user_id', 'agent'])
SLEEP_GAUGE = Gauge("AGENT_sleep_debt_hours", "Sleep Debt", ['user_id', 'agent'])
RECOVERY_GAUGE = Gauge("AGENT_recovery_score", "Recovery Score", ['user_id', 'agent'])

# Risk counters
HRV_RISK = Counter("AGENT_hrv_risk_total", "HRV Risk Events", ['user_id', 'agent', 'severity'])

# Guard OpenTelemetry behind environment flag
if os.getenv("OTEL_ENABLED", "false").lower() == "true":
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor().instrument_app(app)

@app.get("/health")
async def health():
    return {"status": "healthy", "metrics_enabled": True}

@app.get("/kpi/demo")  
async def demo_kpis():
    HRV_GAUGE.labels(user_id="demo", agent="AGENT_name").set(42.0)
    return {"status": "Demo KPIs emitted"}
```

---

## 4 Recommended next sprint checklist

1. **Merge `docs/observability_onboarding.md`** into `main`.  
2. **Instrument NUTROS** using the copy-paste recipe—verify `nutros_glucose_variability_mgdl` appears in Grafana.  
3. **Add disk-free & API-zero-traffic alerts** to Prometheus.  
4. **Enable nightly cron prune** on the host.  
5. **Spin Tempo in staging** (single‐binary Docker Compose example).  

After those five tasks, any agent team can land metrics in 15 min, Grafana shows a full "Nine-Agent KPI Overview," and the platform is hardened against version drift, disk bloat, and silent failures.

---

## 📚 **Reference Links & Support**

- [Prometheus FastAPI Instrumentator](https://pypi.org/project/prometheus-fastapi-instrumentator/)
- [Prometheus Client Python](https://github.com/prometheus/client_python)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Grafana Dashboard Guide](https://grafana.com/docs/grafana/latest/dashboards/)
- [Alert Rules Cookbook](https://awesome-prometheus-alerts.grep.to/rules)

### 📢 **Get Help If...**

* The new agent uses a language other than Python (Java, Go, etc.) – the libraries change.  
* You plan to move to Kubernetes sooner than six months – Helm charts differ slightly.  
* Prometheus will scrape via service discovery instead of static targets – need relabel configs.

Otherwise, the template above works out-of-the-box for your current Compose-based AUREN stack.

---

---

## 🔧 **Enterprise Automation Layer**

### **2.1 Metric Taxonomy Standards**
Follow Prometheus semantic conventions for automatic dashboard templating:

```python
# ✅ CORRECT - Include unit & type in name
HRV_RMSSD = Gauge("neuros_hrv_rmssd_ms", "HRV RMSSD in milliseconds", ['user_id', 'agent'])
SLEEP_DEBT = Gauge("neuros_sleep_debt_hours", "Sleep debt in hours", ['user_id', 'agent'])
RECOVERY_SCORE = Gauge("neuros_recovery_score", "Recovery score 0-100", ['user_id', 'agent'])

# ✅ CORRECT - Risk counters with severity labels  
HRV_RISK = Counter("neuros_hrv_risk_total", "HRV risk events", ['user_id', 'agent', 'severity'])

# ❌ AVOID - No units, unclear meaning
bad_metric = Gauge("hrv", "Some HRV thing")
```

### **2.2 Grafana Provisioning (GitOps)**
Dashboards as code - auto-deploy on startup:

```yaml
# grafana/provisioning/dashboards/auren-kpi.yml
apiVersion: 1
providers:
  - name: 'AUREN KPI Dashboards'
    folder: 'AUREN'
    type: file
    path: /etc/grafana/provisioning/dashboards
```

### **2.3 Prometheus Lifecycle Management**  
Enable hot-reload for zero-downtime config changes:

```bash
# Add to Prometheus startup
--web.enable-lifecycle

# Reload configuration (no restart needed)
curl -X POST http://localhost:9090/-/reload
```

---

## 🎯 **15-Minute Agent Template System**

### **3.1 New Agent Checklist (Copy-Paste)**
For each new agent (NUTROS, KINETOS, etc.):

```bash
# 1. Confirm agent details (30 seconds)
AGENT_NAME="nutros"           # Agent name (lowercase)
AGENT_PORT="8012"            # Unique port number  
METRICS_PATH="/metrics"       # Default path
TRACES_ENABLED="true"        # Enable OpenTelemetry traces

# 2. Add Prometheus scrape job (2 minutes)
echo "
- job_name: \"${AGENT_NAME}-prod\"
  metrics_path: ${METRICS_PATH}
  static_configs:
    - targets: [\"${AGENT_NAME}-container:${AGENT_PORT}\"]
" >> /opt/prometheus.yml

# 3. Reload Prometheus (zero downtime)
curl -X POST http://localhost:9090/-/reload

# 4. Clone Grafana dashboard row (5 minutes)
# Copy KPI panel template, replace neuros -> ${AGENT_NAME}

# 5. Verify metrics (2 minutes)
curl -s http://localhost:${AGENT_PORT}/metrics | grep ${AGENT_NAME}
```

**⏱️ Total time: 15 minutes per agent**

### **3.2 Sanity Test Template**
```bash
# Inside any agent container
curl -s http://localhost:80XX/metrics | head -20
# Look for your KPI lines, e.g., nutros_glucose_variability_mg

# From Prometheus server  
curl -s http://localhost:9090/api/v1/query?query=${AGENT_NAME}_*
```

---

## ⚡ **CI/CD Guard Rails**

✅ **Implemented**: `.github/workflows/observability-gate.yml`

**Automated Protection**:
- **Version Drift**: `pip check` fails on dependency conflicts
- **Security**: Trivy scans block HIGH/CRITICAL CVEs  
- **Metric Taxonomy**: Validates naming conventions (_ms, _total, _hours)
- **High Cardinality**: Warns on explosive label patterns
- **YAML Validation**: yamllint on all configuration files
- **KPI Registry**: Pydantic validation of registry structure

---

## 🚀 **Elite-Team Features**

### **4.1 Grafana Provisioning**
✅ **Implemented**: `grafana/provisioning/dashboards/auren-kpi-overview.yml`

**GitOps Benefits**:
- Dashboards as code (version controlled)
- Auto-reload on file changes (30-second sync)
- Consistent deployment across environments
- No manual Grafana clicking required

### **4.2 Dynamic Service Discovery** (Optional Enhancement)
Auto-detect new agent containers:

```yaml
# prometheus.yml - Advanced configuration
scrape_configs:
  - job_name: 'docker-agents'
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        port: 8000
    relabel_configs:
      - source_labels: [__meta_docker_container_label_auren_agent]
        target_label: agent
```

### **4.3 Dashboard Auto-Generation** (Optional Enhancement)
Generate Grafana panels from KPI registry:

```python
# Advanced: Auto-generate dashboards from YAML
def create_kpi_panel(kpi_name, kpi_config):
    return {
        "title": f"{kpi_config['display_name']}",
        "type": "stat", 
        "targets": [{
            "expr": f"{kpi_name}{{agent=\"$agent\"}}",
            "legendFormat": kpi_config['unit']
        }],
        "fieldConfig": {
            "defaults": {
                "thresholds": {
                    "steps": [
                        {"color": "red", "value": kpi_config['risk_threshold']},
                        {"color": "yellow", "value": kpi_config['caution_threshold']},
                        {"color": "green", "value": kpi_config['optimal_min']}
                    ]
                }
            }
        }
    }
```

---

## 🎯 **What Future Engineers Need**

**For each new agent, send only**:
1. **Host/port** for the agent's `/metrics` endpoint
2. **Metric path** (if not `/metrics`)  
3. **Traces preference** (OTEL_ENABLED=true/false)

**Everything else** is automated:
- Libraries (requirements.otel.txt)
- Dockerfile pattern (python:3.11-slim)
- Prometheus scrape block (template)
- Dashboard template (GitOps)
- CI validation (workflow)

**⏱️ Result**: 15-minute agent onboarding with enterprise-grade observability

---

**🎯 Result**: Every future agent team has a proven, copy-paste recipe for KPI observability. No more trial-and-error, no more dependency conflicts, no more restart loops.

 