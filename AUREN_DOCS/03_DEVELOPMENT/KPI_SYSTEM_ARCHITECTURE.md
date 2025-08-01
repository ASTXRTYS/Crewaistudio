# 📊 KPI System Architecture

**Understanding AUREN's Key Performance Indicator System**

*Created: August 1, 2025*  
*Author: Senior Engineer*

---

## 🎯 Overview

AUREN's KPI system is a two-part architecture that enables agents to track, emit, and respond to biometric and performance metrics. This document explains how KPIs are defined, bound to agents, and flow through the observability pipeline.

---

## 🏗️ Architecture Components

### 1. KPI Registry (`agents/shared_modules/kpi_registry.yaml`)

The **KPI Registry** is the central definition of all available metrics. It defines:
- **What** the metric is (name, description)
- **How** it's measured (unit, prometheus_metric name)
- **Normal ranges** and thresholds
- **Risk levels** and recommended actions

**Example from registry:**
```yaml
- name: "hrv_rmssd"
  description: "Heart Rate Variability - Root Mean Square of Successive Differences"
  unit: "milliseconds"
  category: "autonomic"
  prometheus_metric: "auren_hrv_rmssd_ms"
  normal_range:
    min: 30
    max: 100
    optimal: 50
  risk_thresholds:
    critical:
      condition: "< 20"
      action: "immediate_rest_required"
```

### 2. Agent KPI Bindings (`agents/{agent}_modules/kpi_bindings.yaml`)

The **KPI Bindings** file specifies:
- **Which** KPIs an agent uses
- **How** the agent interprets them (primary signal, trend check, etc.)
- **What actions** to take based on values
- **Cross-agent collaboration** triggers

**Example from NEUROS:**
```yaml
agent: "NEUROS"
kpis_used:
  - key: hrv_rmssd
    role: "primary_signal"
    alerting:
      risk_if: "< 25"
      actions:
        - name: "reduce_training_intensity"
        - name: "trigger_somnos_review"
    
collaboration:
  on_risk:
    - agent: "SOMNOS"
      reason: "Low HRV often linked to poor sleep quality"
```

---

## 🔄 How It Works

### Step 1: Define KPI in Registry
```yaml
# agents/shared_modules/kpi_registry.yaml
- name: "new_metric"
  prometheus_metric: "auren_new_metric"
  unit: "score"
```

### Step 2: Bind to Agent (Optional)
```yaml
# agents/neuros_modules/kpi_bindings.yaml
kpis_used:
  - key: new_metric
    role: "supplementary"
    alerting:
      risk_if: "> 80"
```

### Step 3: Agent Emits Metric
```python
# In agent code
from shared_modules.kpi_emitter import emit
emit("new_metric", calculated_value)
```

### Step 4: Automatic Flow
1. → Prometheus scrapes the metric
2. → Grafana displays on dashboards
3. → Alerts fire based on thresholds
4. → Front-end can query via Metrics Bridge API

---

## 🎨 KPI Types and Roles

### Shared KPIs
- Defined in `shared_modules/kpi_registry.yaml`
- Available to ALL agents
- Examples: HRV, Recovery Score, Sleep Debt

### Agent-Specific KPIs (Future)
- Will be defined in each agent's `kpi_bindings.yaml`
- Unique to that agent
- Examples: 
  - NUTROS: glucose_variability
  - KINETOS: movement_efficiency
  - CARDIOS: vo2_max_estimate

### KPI Roles (in bindings)
- **primary_signal**: Main metric the agent monitors
- **trend_check**: Used for pattern analysis
- **composite_gate**: Derived metric for decisions
- **supplementary**: Additional context

---

## 📡 Observability Pipeline

```
KPI Registry → Agent Emits → Prometheus → Grafana
                    ↓
              Metrics Bridge API
                    ↓
              Front-End Display
```

---

## 🔧 Adding a New KPI

### For Shared KPIs:
1. Add to `agents/shared_modules/kpi_registry.yaml`
2. Run validation: `python3 scripts/validate_kpi_registry.py`
3. Generate configs: `python3 scripts/generate_dashboards.py`
4. Deploy: `./auren-pwa/observability-as-code/scripts/deploy-configs.sh`

### For Agent-Specific KPIs:
1. Create/update `agents/{agent}_modules/kpi_bindings.yaml`
2. Define the binding and alerting rules
3. Update agent code to emit the metric
4. Follow shared KPI steps 2-4

---

## 📊 Current KPI Status

### Implemented:
- ✅ NEUROS: Using shared KPIs (HRV, Recovery, Sleep Debt)
- ✅ KPI Registry: 3 shared metrics defined
- ✅ Observability Pipeline: Fully automated

### Pending:
- ⏳ NUTROS: Awaiting metabolic KPIs
- ⏳ KINETOS: Awaiting movement KPIs
- ⏳ Other agents: Awaiting implementation

---

## 🚀 Best Practices

1. **Define Once, Use Everywhere**: Add to registry first
2. **Meaningful Thresholds**: Base on scientific literature
3. **Clear Actions**: Each threshold should trigger specific responses
4. **Cross-Agent Awareness**: Define collaboration triggers
5. **Version Control**: Track changes to KPI definitions

---

## 📚 Related Documentation

- [Observability-as-Code Guide](../../auren-pwa/observability-as-code/README.md)
- [KPI Registry](../../agents/shared_modules/kpi_registry.yaml)
- [NEUROS KPI Bindings](../../agents/neuros_modules/kpi_bindings.yaml)

---

*This architecture enables any engineer to add new metrics that automatically flow through the entire AUREN system.*