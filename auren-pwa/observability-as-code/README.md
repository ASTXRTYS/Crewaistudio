# 🔭 AUREN Observability-as-Code Documentation

**The Complete Guide to AUREN's Automated Observability Pipeline**

---

## 🎯 What is Observability-as-Code?

Observability-as-Code means that adding ONE line to a YAML file automatically creates:
- ✅ Backend metrics collection
- ✅ Prometheus storage & queries
- ✅ Grafana dashboards
- ✅ Alert rules
- ✅ Recording rules for performance
- ✅ Front-end display capability

**No manual configuration. No clicking around. Just code.**

---

## 📁 Directory Structure

```
observability-as-code/
├── README.md                           # This file
├── QUICK_START.md                      # 5-minute guide for engineers
├── ARCHITECTURE.md                     # How everything connects
├── TROUBLESHOOTING.md                  # Common issues & solutions
├── examples/
│   ├── add-new-kpi.md                 # How to add a new KPI
│   ├── frontend-integration.md         # Adding metrics to front-end
│   └── agent-specific-kpis.md         # Per-agent KPI setup
├── scripts/
│   ├── validate-kpi.sh                # Validate KPI registry
│   ├── generate-all.sh               # Generate everything
│   └── deploy-configs.sh             # Deploy to production
└── templates/
    ├── kpi-template.yaml              # KPI definition template
    ├── metric-component.jsx           # React component template
    └── dashboard-panel.json           # Grafana panel template
```

---

## 🚀 Quick Examples

### Adding a New KPI (Backend → Frontend in 5 minutes)

1. **Add to KPI Registry** (`agents/shared_modules/kpi_registry.yaml`):
```yaml
- name: "cognitive_load"
  description: "Real-time cognitive processing load"
  unit: "percentage"
  category: "cognitive"
  prometheus_metric: "auren_cognitive_load_percent"
  normal_range:
    min: 0
    max: 70
    optimal: 30
  risk_thresholds:
    critical:
      condition: "> 90"
      action: "immediate_break_required"
    warning:
      condition: "> 70"
      action: "reduce_task_complexity"
```

2. **Generate Configurations**:
```bash
cd /path/to/CrewAI-Studio-main
python3 scripts/generate_dashboards.py --input agents/shared_modules/kpi_registry.yaml --output grafana/dashboards/kpi-generated.json
python3 scripts/generate_recording_rules.py --input agents/shared_modules/kpi_registry.yaml --output prometheus/rules/kpi-generated.yml
python3 scripts/generate_alerts.py --input agents/shared_modules/kpi_registry.yaml --output prometheus/alerts/kpi-generated.yml
```

3. **Deploy to Server**:
```bash
./auren-pwa/observability-as-code/scripts/deploy-configs.sh
```

4. **Add to Front-End** (one line in your React component):
```jsx
<MetricChart metricName="auren_cognitive_load_percent" userId={userId} />
```

That's it! The metric now flows automatically through the entire system.

---

## 🏗️ Architecture Overview

```
┌─────────────────────┐
│   KPI Registry      │  ← You edit this YAML file
│ (kpi_registry.yaml) │
└──────────┬──────────┘
           │
           ▼ Auto-generates
┌──────────────────────────────────────────┐
│  Generator Scripts                       │
├──────────────┬───────────────────────────┤
│ Dashboards   │ Recording Rules │ Alerts  │
└──────┬───────┴────────┬────────┴─────────┘
       │                │
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│  Grafana    │  │ Prometheus  │
│ (Port 3000) │  │ (Port 9090) │
└─────────────┘  └──────┬──────┘
                        │
                        ▼
              ┌─────────────────┐
              │ Metrics Bridge  │
              │  (Port 8002)    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   Front-End     │
              │ (Your Choice)   │
              └─────────────────┘
```

---

## 🔌 Current Infrastructure

| Service | Port | Purpose | Container Name |
|---------|------|---------|----------------|
| NEUROS | 8000 | AI Agent (emits metrics) | `neuros-advanced` |
| Metrics Bridge | 8002 | Front-end API | `auren-metrics-bridge` |
| Biometric Bridge | 8888 | Biometric processing | `biometric-production` |
| Prometheus | 9090 | Metric storage | `auren-prometheus` |
| Grafana | 3000 | Dashboards | `auren-grafana` |
| OTel Collector | 4318 | Trace collection | `auren-otel-collector` |

---

## 📊 Currently Observable Metrics

### Shared KPIs (All Agents)
- `auren_hrv_rmssd_ms` - Heart Rate Variability
- `auren_recovery_score` - Recovery Score (0-100)
- `auren_sleep_debt_hours` - Sleep Debt

### Future Agent-Specific KPIs
When you create YAML profiles for other agents (NUTROS, KINETOS, etc.), they can have their own KPIs:
```yaml
# Example: agents/nutros_modules/kpi_bindings.yaml
- name: "glucose_stability"
  prometheus_metric: "auren_glucose_cv"
```

---

## 🛠️ Common Tasks

### 1. "I added a KPI but it's not showing up"
See: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#kpi-not-showing)

### 2. "How do I add metrics to a specific page?"
See: [examples/frontend-integration.md](./examples/frontend-integration.md)

### 3. "Can each agent have its own KPIs?"
See: [examples/agent-specific-kpis.md](./examples/agent-specific-kpis.md)

### 4. "The metric value shows as '--' on frontend"
See: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#no-data)

---

## 🔑 Key Files You'll Work With

1. **KPI Registry**: `agents/shared_modules/kpi_registry.yaml`
   - The source of truth for all metrics
   
2. **Generator Scripts**: `scripts/generate_*.py`
   - Transform YAML → Configurations
   
3. **Metrics Bridge API**: `auren/api/metrics_bridge.py`
   - Serves metrics to front-end
   
4. **Front-End Examples**: `AUPEX_WEBSITE_METRIC_INTEGRATION_EXAMPLE.md`
   - Copy-paste React code

---

## 🚨 Important Notes

1. **Agent Readiness**: Currently only NEUROS has a complete YAML profile. Other agents need their profiles created first.

2. **Port Configuration**: Everything routes through specific ports:
   - NEUROS: 8000
   - Metrics Bridge: 8002
   - Don't change these without updating all references!

3. **Security**: The Metrics Bridge filters what's exposed. Not all backend metrics are available to front-end by default.

---

## 📞 Getting Help

1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) first
2. Review the [examples/](./examples/) folder
3. Look at working code in `auren/dashboard_v2/js/neuroscientist.js`

---

*"One YAML line → Complete observability. That's the power of code."*