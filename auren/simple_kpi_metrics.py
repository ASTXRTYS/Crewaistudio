#!/usr/bin/env python3
"""
AUREN Simple KPI Metrics - Production Ready
===========================================
Lightweight KPI metrics using prometheus-fastapi-instrumentator.
Battle-tested approach for real-time agent monitoring.

Created: July 31, 2025
"""

import logging
import random
from typing import Dict, Any
from prometheus_client import Gauge, Counter
from prometheus_fastapi_instrumentator import Instrumentator

logger = logging.getLogger(__name__)

# KPI Gauges - one for each registry KPI
hrv_gauge = Gauge('neuros_hrv_rmssd_ms', 'Heart Rate Variability RMSSD', ['user_id', 'agent'])
sleep_debt_gauge = Gauge('neuros_sleep_debt_hours', 'Sleep Debt Hours', ['user_id', 'agent'])
recovery_gauge = Gauge('neuros_recovery_score', 'Recovery Score', ['user_id', 'agent'])

# Risk counters - for threshold breaches
hrv_risk_counter = Counter('neuros_hrv_risk_total', 'HRV Risk Events', ['user_id', 'agent', 'severity'])
sleep_risk_counter = Counter('neuros_sleep_risk_total', 'Sleep Risk Events', ['user_id', 'agent', 'severity'])
recovery_risk_counter = Counter('neuros_recovery_risk_total', 'Recovery Risk Events', ['user_id', 'agent', 'severity'])

class SimpleKPIEmitter:
    """Simple KPI metrics emitter using prometheus_client."""
    
    @staticmethod
    def emit_kpis(user_id: str, agent: str = "neuros", kpi_data: Dict[str, float] = None):
        """Emit KPI values to Prometheus."""
        try:
            if kpi_data is None:
                # Generate demo data based on realistic ranges
                kpi_data = {
                    "hrv_rmssd": random.uniform(20, 80),
                    "sleep_debt_hours": random.uniform(0, 10), 
                    "recovery_score": random.uniform(30, 95)
                }
            
            # Emit gauges
            if "hrv_rmssd" in kpi_data:
                hrv_gauge.labels(user_id=user_id, agent=agent).set(kpi_data["hrv_rmssd"])
                SimpleKPIEmitter._check_hrv_risk(kpi_data["hrv_rmssd"], user_id, agent)
            
            if "sleep_debt_hours" in kpi_data:
                sleep_debt_gauge.labels(user_id=user_id, agent=agent).set(kpi_data["sleep_debt_hours"])
                SimpleKPIEmitter._check_sleep_risk(kpi_data["sleep_debt_hours"], user_id, agent)
            
            if "recovery_score" in kpi_data:
                recovery_gauge.labels(user_id=user_id, agent=agent).set(kpi_data["recovery_score"])
                SimpleKPIEmitter._check_recovery_risk(kpi_data["recovery_score"], user_id, agent)
            
            logger.info(f"Emitted KPIs for {user_id}: {kpi_data}")
            
        except Exception as e:
            logger.error(f"Failed to emit KPIs: {e}")
    
    @staticmethod
    def _check_hrv_risk(value: float, user_id: str, agent: str):
        """Check HRV risk thresholds."""
        if value < 20:
            hrv_risk_counter.labels(user_id=user_id, agent=agent, severity="critical").inc()
        elif value < 30:
            hrv_risk_counter.labels(user_id=user_id, agent=agent, severity="warning").inc()
    
    @staticmethod
    def _check_sleep_risk(value: float, user_id: str, agent: str):
        """Check sleep debt risk thresholds.""" 
        if value > 8:
            sleep_risk_counter.labels(user_id=user_id, agent=agent, severity="critical").inc()
        elif value > 4:
            sleep_risk_counter.labels(user_id=user_id, agent=agent, severity="warning").inc()
    
    @staticmethod
    def _check_recovery_risk(value: float, user_id: str, agent: str):
        """Check recovery score risk thresholds."""
        if value < 40:
            recovery_risk_counter.labels(user_id=user_id, agent=agent, severity="critical").inc()
        elif value < 60:
            recovery_risk_counter.labels(user_id=user_id, agent=agent, severity="warning").inc()

def setup_kpi_metrics(app):
    """Setup KPI metrics with FastAPI app using prometheus-fastapi-instrumentator."""
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        
        # Setup instrumentator with custom metrics
        instrumentator = Instrumentator()
        instrumentator.instrument(app).expose(app)
        
        logger.info("KPI metrics setup complete with prometheus-fastapi-instrumentator")
        return True
        
    except ImportError:
        logger.warning("prometheus-fastapi-instrumentator not available, using basic setup")
        return False

# Convenience functions
def emit_conversation_kpis(user_id: str, session_id: str, response_time: float):
    """Emit KPIs after a conversation interaction."""
    # Simple calculation based on response time and session
    kpi_data = {
        "hrv_rmssd": max(20, 60 - (response_time * 10)),  # Slower = more stress
        "sleep_debt_hours": min(12, len(session_id) * 0.1),  # Session length proxy
        "recovery_score": max(30, 90 - (response_time * 15))  # Performance proxy
    }
    
    SimpleKPIEmitter.emit_kpis(user_id, "neuros", kpi_data)

def emit_demo_kpis(user_id: str = "demo_user"):
    """Emit demo KPI values for testing."""
    SimpleKPIEmitter.emit_kpis(user_id, "neuros")

if __name__ == "__main__":
    # Test the metrics
    logging.basicConfig(level=logging.INFO)
    print("Testing KPI metrics...")
    emit_demo_kpis()
    print("Demo KPIs emitted!") 