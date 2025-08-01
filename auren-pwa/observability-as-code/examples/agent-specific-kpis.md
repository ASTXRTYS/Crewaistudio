# 🤖 Agent-Specific KPIs Guide

**How to add KPIs for individual agents**

---

## 📋 Current Status

- ✅ **NEUROS**: Fully implemented with shared KPIs
- ⏳ **NUTROS**: Awaiting YAML profile
- ⏳ **KINETOS**: Awaiting YAML profile
- ⏳ **HYPERTROS**: Awaiting YAML profile
- ⏳ **CARDIOS**: Awaiting YAML profile
- ⏳ **SOMNOS**: Awaiting YAML profile
- ⏳ **OPTICOS**: Awaiting YAML profile
- ⏳ **ENDOS**: Awaiting YAML profile
- ⏳ **AUREN**: Master orchestrator (awaiting implementation)

---

## 🚀 How Agent-Specific KPIs Will Work

### 1. Create Agent KPI Bindings

Each agent will have its own KPI bindings file:

```yaml
# agents/nutros_modules/kpi_bindings.yaml
agent: nutros
version: "1.0"
kpis:
  - name: "glucose_variability"
    description: "Coefficient of variation in glucose levels"
    unit: "percentage"
    prometheus_metric: "auren_nutros_glucose_cv"
    category: "metabolic"
    normal_range:
      min: 0
      max: 36
      optimal: 20
    risk_thresholds:
      critical:
        condition: "> 50"
        action: "urgent_dietary_intervention"
      warning:
        condition: "> 36"
        action: "review_meal_timing"
  
  - name: "insulin_sensitivity"
    description: "Insulin sensitivity index"
    unit: "score"
    prometheus_metric: "auren_nutros_insulin_sensitivity"
    category: "metabolic"
    normal_range:
      min: 0.5
      max: 2.0
      optimal: 1.2
```

### 2. Update Agent Implementation

In the agent's code, use the KPI emitter:

```python
# agents/nutros/nutros_agent.py
from shared_modules.kpi_emitter import emit
import yaml
from pathlib import Path

class NutrosAgent:
    def __init__(self):
        # Load agent-specific KPIs
        self.load_agent_kpis()
    
    def load_agent_kpis(self):
        """Load agent-specific KPI bindings"""
        kpi_path = Path(__file__).parent / "nutros_modules" / "kpi_bindings.yaml"
        if kpi_path.exists():
            with open(kpi_path) as f:
                self.kpi_config = yaml.safe_load(f)
    
    def analyze_glucose_data(self, readings):
        """Analyze glucose variability"""
        # Calculate coefficient of variation
        cv = (np.std(readings) / np.mean(readings)) * 100
        
        # Emit the metric
        emit("glucose_variability", cv)
        
        return cv
    
    def calculate_insulin_sensitivity(self, glucose, insulin):
        """Calculate insulin sensitivity index"""
        # HOMA-IR calculation (simplified)
        sensitivity = 1 / ((glucose * insulin) / 405)
        
        # Emit the metric
        emit("insulin_sensitivity", sensitivity)
        
        return sensitivity
```

### 3. Aggregate All Agent KPIs

Create a master script to combine all agent KPIs:

```python
# scripts/aggregate_agent_kpis.py
#!/usr/bin/env python3
"""
Aggregate all agent-specific KPIs into the main registry
"""
import yaml
from pathlib import Path

def aggregate_kpis():
    # Start with shared KPIs
    main_registry = Path("agents/shared_modules/kpi_registry.yaml")
    with open(main_registry) as f:
        registry = yaml.safe_load(f)
    
    # Find all agent KPI bindings
    agent_kpis = []
    for agent_dir in Path("agents").glob("*_modules"):
        kpi_file = agent_dir / "kpi_bindings.yaml"
        if kpi_file.exists():
            with open(kpi_file) as f:
                agent_data = yaml.safe_load(f)
                # Prefix metrics with agent name
                for kpi in agent_data.get("kpis", []):
                    kpi["agent"] = agent_data["agent"]
                    agent_kpis.extend(agent_data.get("kpis", []))
    
    # Combine all KPIs
    all_kpis = registry["kpis"] + agent_kpis
    
    # Save aggregated registry
    aggregated = {
        **registry,
        "kpis": all_kpis,
        "total_kpis": len(all_kpis),
        "agents_with_kpis": len(set(kpi.get("agent", "shared") for kpi in all_kpis))
    }
    
    with open("agents/shared_modules/kpi_registry_aggregated.yaml", "w") as f:
        yaml.dump(aggregated, f, default_flow_style=False)
    
    print(f"✅ Aggregated {len(all_kpis)} KPIs from {aggregated['agents_with_kpis']} agents")

if __name__ == "__main__":
    aggregate_kpis()
```

---

## 🎯 Example: Adding KINETOS KPIs

### Step 1: Create KPI Bindings

```yaml
# agents/kinetos_modules/kpi_bindings.yaml
agent: kinetos
version: "1.0"
kpis:
  - name: "movement_efficiency"
    description: "Biomechanical efficiency score"
    unit: "percentage"
    prometheus_metric: "auren_kinetos_movement_efficiency"
    category: "biomechanics"
    
  - name: "muscle_activation_balance"
    description: "Left/right muscle activation symmetry"
    unit: "percentage"
    prometheus_metric: "auren_kinetos_muscle_balance"
    category: "biomechanics"
    
  - name: "power_output"
    description: "Peak power output"
    unit: "watts"
    prometheus_metric: "auren_kinetos_power_watts"
    category: "performance"
```

### Step 2: Update KINETOS Agent

```python
# agents/kinetos/kinetos_agent.py
from shared_modules.kpi_emitter import emit

class KinetosAgent:
    def analyze_movement(self, motion_data):
        # Calculate efficiency
        efficiency = self.calculate_efficiency(motion_data)
        emit("movement_efficiency", efficiency)
        
        # Check muscle balance
        balance = self.calculate_muscle_balance(motion_data)
        emit("muscle_activation_balance", balance)
        
        # Measure power
        power = self.calculate_power_output(motion_data)
        emit("power_output", power)
```

### Step 3: Deploy

```bash
# Aggregate all KPIs
python3 scripts/aggregate_agent_kpis.py

# Generate configs using aggregated registry
python3 scripts/generate_dashboards.py \
  --input agents/shared_modules/kpi_registry_aggregated.yaml \
  --output grafana/dashboards/all-agents-dashboard.json

# Deploy
./auren-pwa/observability-as-code/scripts/deploy-configs.sh
```

---

## 📊 Front-End Display by Agent

### Agent Selector Component

```javascript
// Show metrics for specific agent
function AgentMetrics({ agentName }) {
    const [metrics, setMetrics] = useState([]);
    
    useEffect(() => {
        // Get agent-specific metrics
        fetch('http://144.126.215.218:8002/api/metrics/catalog')
            .then(res => res.json())
            .then(data => {
                const agentMetrics = data.metrics.filter(m => 
                    m.metric.includes(`auren_${agentName.toLowerCase()}_`)
                );
                setMetrics(agentMetrics);
            });
    }, [agentName]);
    
    return (
        <div className="agent-metrics">
            <h2>{agentName} Metrics</h2>
            {metrics.map(metric => (
                <MetricDisplay 
                    key={metric.id}
                    metricName={metric.metric}
                    title={metric.name}
                />
            ))}
        </div>
    );
}
```

---

## 🔮 Future: Dynamic Agent KPI Loading

When all agents are implemented, the system will:

1. **Auto-discover** agent KPI files on startup
2. **Dynamically load** new KPIs without restart
3. **Namespace metrics** by agent (e.g., `auren_nutros_*`, `auren_kinetos_*`)
4. **Generate agent-specific dashboards** automatically
5. **Create cross-agent correlation** dashboards

---

## 📝 Checklist for New Agent KPIs

- [ ] Create `agents/{agent}_modules/kpi_bindings.yaml`
- [ ] Define agent-specific metrics with proper namespacing
- [ ] Update agent code to use `kpi_emitter`
- [ ] Run aggregation script
- [ ] Regenerate dashboards and rules
- [ ] Deploy configurations
- [ ] Test metric emission
- [ ] Add to front-end display

---

*Note: Until each agent has a complete YAML profile and implementation, agent-specific KPIs won't be functional. Focus on NEUROS and shared KPIs for now.*