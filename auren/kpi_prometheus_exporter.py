#!/usr/bin/env python3
"""
AUREN KPI Prometheus Exporter
Exports KPI metrics to Prometheus based on kpi_registry.yaml
"""

import yaml
import time
from prometheus_client import Gauge, CollectorRegistry, generate_latest
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class KPIPrometheusExporter:
    """Export AUREN KPIs as Prometheus metrics"""
    
    def __init__(self, registry_path: str = "agents/shared_modules/kpi_registry.yaml"):
        self.registry = CollectorRegistry()
        self.metrics: Dict[str, Gauge] = {}
        self.load_kpi_registry(registry_path)
        
    def load_kpi_registry(self, path: str):
        """Load KPI definitions from YAML registry"""
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                
            for kpi in data.get('kpis', []):
                metric_name = kpi['prometheus_metric']
                description = kpi['description']
                
                # Create Prometheus gauge
                gauge = Gauge(
                    metric_name,
                    description,
                    labelnames=['user_id', 'measurement_source', 'agent'],
                    registry=self.registry
                )
                
                self.metrics[kpi['name']] = gauge
                logger.info(f"Registered KPI metric: {metric_name}")
                
        except Exception as e:
            logger.error(f"Failed to load KPI registry: {e}")
            
    def update_kpi(self, kpi_name: str, value: float, user_id: str, 
                   measurement_source: str = "auren", agent: str = "unknown"):
        """Update a KPI metric value"""
        if kpi_name in self.metrics:
            self.metrics[kpi_name].labels(
                user_id=user_id,
                measurement_source=measurement_source,
                agent=agent
            ).set(value)
            logger.debug(f"Updated {kpi_name}={value} for user {user_id}")
        else:
            logger.warning(f"Unknown KPI: {kpi_name}")
            
    def get_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        return generate_latest(self.registry).decode('utf-8')
        
    def validate_kpi_binding(self, binding_data: Dict[str, Any]) -> bool:
        """Validate KPI binding against registry"""
        kpi_used = binding_data.get('kpi_used')
        if not kpi_used:
            logger.error("Missing kpi_used field in binding")
            return False
            
        if kpi_used not in self.metrics:
            logger.error(f"KPI {kpi_used} not found in registry")
            return False
            
        # Validate thresholds structure
        thresholds = binding_data.get('thresholds', {})
        if 'risk_if' not in thresholds:
            logger.error("Missing risk_if condition in thresholds")
            return False
            
        logger.info(f"KPI binding validation passed for {kpi_used}")
        return True

# Example usage and testing
if __name__ == "__main__":
    exporter = KPIPrometheusExporter()
    
    # Example KPI updates
    exporter.update_kpi("hrv_rmssd", 45.2, "user_123", "apple_watch", "neuros")
    exporter.update_kpi("sleep_debt_hours", 2.5, "user_123", "oura", "somnos")
    exporter.update_kpi("recovery_score", 78, "user_123", "whoop", "neuros")
    
    # Example binding validation
    binding = {
        "kpi_used": "hrv_rmssd",
        "thresholds": {
            "risk_if": "< 25"
        },
        "actions": [
            {"name": "reduce_training_intensity"}
        ]
    }
    
    if exporter.validate_kpi_binding(binding):
        print("✅ KPI binding valid")
    
    print("Generated Prometheus metrics:")
    print(exporter.get_metrics()) 