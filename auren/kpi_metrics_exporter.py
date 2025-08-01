#!/usr/bin/env python3
"""
AUREN KPI Metrics Exporter - Production Ready
==============================================
Real-time KPI metrics emission for agent protocol visualization.
Integrates with existing OpenTelemetry/Prometheus infrastructure.

Created: July 31, 2025
Purpose: Enable real-time monitoring of AI agent KPIs in Grafana
"""

import logging
import yaml
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from opentelemetry import metrics
from opentelemetry.metrics import Gauge, Counter, Histogram

logger = logging.getLogger(__name__)

class KPIMetricsExporter:
    """
    Production-ready KPI metrics exporter for AUREN agents.
    
    Features:
    - Real-time KPI emission to Prometheus
    - Threshold breach detection and counting
    - Agent-specific labeling
    - Registry-driven configuration
    """
    
    def __init__(self, registry_path: str = "agents/shared_modules/kpi_registry.yaml"):
        """Initialize KPI metrics exporter."""
        self.registry_path = Path(registry_path)
        self.meter = metrics.get_meter("auren.kpi.metrics")
        self.kpi_registry = self._load_kpi_registry()
        self.metrics = self._initialize_metrics()
        
        logger.info(f"KPI Metrics Exporter initialized with {len(self.kpi_registry['kpis'])} KPIs")
    
    def _load_kpi_registry(self) -> Dict[str, Any]:
        """Load KPI registry from YAML."""
        try:
            with open(self.registry_path, 'r') as f:
                registry = yaml.safe_load(f)
            logger.info(f"Loaded KPI registry v{registry.get('version', 'unknown')}")
            return registry
        except Exception as e:
            logger.error(f"Failed to load KPI registry: {e}")
            return {"kpis": [], "export_config": {"prometheus": {"enabled": False}}}
    
    def _initialize_metrics(self) -> Dict[str, Any]:
        """Initialize Prometheus metrics from KPI registry."""
        metrics_dict = {}
        
        if not self.kpi_registry.get("export_config", {}).get("prometheus", {}).get("enabled", False):
            logger.warning("Prometheus export disabled in KPI registry")
            return metrics_dict
        
        for kpi in self.kpi_registry["kpis"]:
            kpi_name = kpi["name"]
            prometheus_metric = kpi["prometheus_metric"]
            description = kpi["description"]
            unit = kpi["unit"]
            
            # Create gauge for KPI value
            gauge = self.meter.create_gauge(
                name=prometheus_metric,
                description=f"{description} ({unit})",
                unit=unit
            )
            metrics_dict[f"{kpi_name}_gauge"] = gauge
            
            # Create counter for threshold breaches
            breach_counter = self.meter.create_counter(
                name=f"{prometheus_metric}_risk_total",
                description=f"Total threshold breaches for {kpi_name}",
                unit="1"
            )
            metrics_dict[f"{kpi_name}_breach_counter"] = breach_counter
            
            # Create histogram for value distribution
            histogram = self.meter.create_histogram(
                name=f"{prometheus_metric}_distribution",
                description=f"Value distribution for {kpi_name}",
                unit=unit
            )
            metrics_dict[f"{kpi_name}_histogram"] = histogram
            
            logger.info(f"Initialized metrics for KPI: {kpi_name}")
        
        return metrics_dict
    
    def emit_kpi_value(self, 
                       kpi_name: str, 
                       value: float, 
                       user_id: str, 
                       agent: str = "neuros",
                       measurement_source: str = "calculated") -> None:
        """
        Emit a KPI value to Prometheus.
        
        Args:
            kpi_name: Name of the KPI (e.g., "hrv_rmssd")
            value: The KPI value
            user_id: User identifier
            agent: Agent name that calculated the KPI
            measurement_source: Source of the measurement
        """
        try:
            # Find KPI configuration
            kpi_config = self._get_kpi_config(kpi_name)
            if not kpi_config:
                logger.error(f"KPI '{kpi_name}' not found in registry")
                return
            
            # Common labels
            labels = {
                "user_id": user_id,
                "agent": agent,
                "measurement_source": measurement_source,
                "kpi_name": kpi_name
            }
            
            # Emit gauge value
            gauge_key = f"{kpi_name}_gauge"
            if gauge_key in self.metrics:
                self.metrics[gauge_key].set(value, labels)
                logger.debug(f"Emitted KPI {kpi_name}: {value} {kpi_config['unit']}")
            
            # Emit histogram value
            histogram_key = f"{kpi_name}_histogram"
            if histogram_key in self.metrics:
                self.metrics[histogram_key].record(value, labels)
            
            # Check for threshold breaches
            self._check_and_emit_breaches(kpi_name, value, labels, kpi_config)
            
        except Exception as e:
            logger.error(f"Failed to emit KPI {kpi_name}: {e}")
    
    def emit_multiple_kpis(self, kpi_data: Dict[str, float], 
                          user_id: str, 
                          agent: str = "neuros",
                          measurement_source: str = "calculated") -> None:
        """
        Emit multiple KPI values in batch.
        
        Args:
            kpi_data: Dictionary of {kpi_name: value}
            user_id: User identifier
            agent: Agent name
            measurement_source: Source of measurements
        """
        for kpi_name, value in kpi_data.items():
            self.emit_kpi_value(kpi_name, value, user_id, agent, measurement_source)
    
    def _get_kpi_config(self, kpi_name: str) -> Optional[Dict[str, Any]]:
        """Get KPI configuration from registry."""
        for kpi in self.kpi_registry["kpis"]:
            if kpi["name"] == kpi_name:
                return kpi
        return None
    
    def _check_and_emit_breaches(self, kpi_name: str, value: float, 
                                labels: Dict[str, str], kpi_config: Dict[str, Any]) -> None:
        """Check for threshold breaches and emit counter increments."""
        breach_counter_key = f"{kpi_name}_breach_counter"
        if breach_counter_key not in self.metrics:
            return
        
        risk_thresholds = kpi_config.get("risk_thresholds", {})
        
        for severity, threshold_config in risk_thresholds.items():
            condition = threshold_config.get("condition", "")
            action = threshold_config.get("action", "unknown")
            
            if self._evaluate_threshold_condition(value, condition):
                # Add severity and action to labels
                breach_labels = {**labels, "severity": severity, "action": action}
                self.metrics[breach_counter_key].add(1, breach_labels)
                
                logger.warning(f"KPI {kpi_name} breach: {value} triggers {severity} ({condition}) -> {action}")
                break  # Only count the highest severity breach
    
    def _evaluate_threshold_condition(self, value: float, condition: str) -> bool:
        """Evaluate a threshold condition string."""
        try:
            # Replace condition operators and evaluate
            condition = condition.strip()
            if condition.startswith("< "):
                threshold = float(condition[2:])
                return value < threshold
            elif condition.startswith("> "):
                threshold = float(condition[2:])
                return value > threshold
            elif condition.startswith("≤ ") or condition.startswith("<= "):
                threshold = float(condition[2:])
                return value <= threshold
            elif condition.startswith("≥ ") or condition.startswith(">= "):
                threshold = float(condition[2:])
                return value >= threshold
            else:
                logger.warning(f"Unknown condition format: {condition}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def emit_demo_kpis(self, user_id: str = "demo_user") -> None:
        """Emit demo KPI values for testing dashboard visualization."""
        import random
        
        demo_data = {
            "hrv_rmssd": random.uniform(20, 80),  # Mix of normal and low values
            "sleep_debt_hours": random.uniform(0, 10),  # Some high debt
            "recovery_score": random.uniform(30, 95)  # Mix of scores
        }
        
        logger.info(f"Emitting demo KPIs: {demo_data}")
        self.emit_multiple_kpis(demo_data, user_id, "neuros", "demo_generator")
    
    def get_metrics_info(self) -> Dict[str, Any]:
        """Get information about configured metrics."""
        return {
            "registry_version": self.kpi_registry.get("version", "unknown"),
            "kpi_count": len(self.kpi_registry["kpis"]),
            "metrics_configured": len(self.metrics),
            "prometheus_enabled": self.kpi_registry.get("export_config", {}).get("prometheus", {}).get("enabled", False),
            "kpi_names": [kpi["name"] for kpi in self.kpi_registry["kpis"]]
        }

# Global instance for use across the application
kpi_exporter = None

def get_kpi_exporter() -> KPIMetricsExporter:
    """Get global KPI exporter instance."""
    global kpi_exporter
    if kpi_exporter is None:
        kpi_exporter = KPIMetricsExporter()
    return kpi_exporter

def emit_kpi(kpi_name: str, value: float, user_id: str, 
             agent: str = "neuros", measurement_source: str = "calculated") -> None:
    """Convenience function to emit a single KPI."""
    exporter = get_kpi_exporter()
    exporter.emit_kpi_value(kpi_name, value, user_id, agent, measurement_source)

def emit_agent_kpis(kpi_data: Dict[str, float], user_id: str, 
                    agent: str = "neuros", measurement_source: str = "calculated") -> None:
    """Convenience function to emit multiple KPIs."""
    exporter = get_kpi_exporter()
    exporter.emit_multiple_kpis(kpi_data, user_id, agent, measurement_source)

if __name__ == "__main__":
    # Demo/testing
    logging.basicConfig(level=logging.INFO)
    exporter = KPIMetricsExporter()
    
    print("KPI Metrics Exporter Demo")
    print("=========================")
    print(f"Metrics info: {exporter.get_metrics_info()}")
    
    # Emit demo values
    exporter.emit_demo_kpis()
    print("Demo KPIs emitted - check Prometheus /metrics endpoint") 