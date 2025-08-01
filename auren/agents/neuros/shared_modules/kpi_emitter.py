# shared_modules/kpi_emitter.py
from prometheus_client import Gauge
import yaml
import pathlib

# Load KPI registry
registry_data = yaml.safe_load(
    pathlib.Path("/app/shared_modules/kpi_registry.yaml").read_text()
)

# Extract KPIs list
kpis = registry_data.get("kpis", [])

# Create Prometheus gauges (no labels for zero cardinality)
GAUGES = {}
for kpi in kpis:
    metric_name = kpi.get("prometheus_metric", f"auren_{kpi['name']}")
    GAUGES[kpi["name"]] = Gauge(metric_name, kpi["description"])

def emit(key: str, value: float):
    """Emit a KPI metric value to Prometheus"""
    if key in GAUGES:
        GAUGES[key].set(value)