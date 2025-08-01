#!/usr/bin/env python3
"""
KPI Emitter - Simple 40-LOC Module
==================================
Loads YAML registry and exposes emit(key, value) gauges.
Identical to proven simple service pattern.
"""

from prometheus_client import Gauge
import yaml
import pathlib
import logging

logger = logging.getLogger(__name__)

# Load KPI registry from YAML
try:
    registry_path = pathlib.Path("/app/shared_modules/kpi_registry.yaml")
    if not registry_path.exists():
        # Fallback for development
        registry_path = pathlib.Path("kpi_registry.yaml")
    
    REGISTRY = yaml.safe_load(registry_path.read_text())["kpis"]
    logger.info(f"Loaded {len(REGISTRY)} KPIs from {registry_path}")
except Exception as e:
    logger.error(f"Failed to load KPI registry: {e}")
    REGISTRY = []

# Create Prometheus gauges
GAUGES = {}
for kpi in REGISTRY:
    key = kpi["name"]
    description = kpi["description"]
    unit = kpi.get("unit", "")
    
    gauge = Gauge(
        name=f"neuros_{key}",
        documentation=f"{description} ({unit})",
        labelnames=['user_id', 'agent']
    )
    GAUGES[key] = gauge
    logger.debug(f"Created gauge for {key}")

def emit(key: str, value: float, user_id: str = "default", agent: str = "neuros"):
    """
    Emit KPI value to Prometheus gauge.
    
    Args:
        key: KPI name (e.g., "hrv_rmssd")
        value: KPI value
        user_id: User identifier
        agent: Agent name
    """
    if key in GAUGES:
        GAUGES[key].labels(user_id=user_id, agent=agent).set(value)
        logger.debug(f"Emitted {key}={value} for user {user_id}")
    else:
        logger.warning(f"Unknown KPI key: {key}")

def get_available_kpis():
    """Return list of available KPI keys."""
    return list(GAUGES.keys())