"""
Pydantic Models for KPI Registry and Bindings Validation

This module provides the validation layer for the two-part KPI system:
1. kpi_registry.yaml: The canonical atlas of all metrics.
2. kpi_bindings.yaml: The agent-specific logic for how to use those metrics.

Running this file directly will test the validation against the current YAML files.
"""
import os
import yaml
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

# --- KPI Registry Models (The "What") -----------------------------------------

class KPIThresholds(BaseModel):
    optimal: Optional[Any] = None
    caution: Optional[Any] = None
    risk: Optional[Any] = None
    risk_if: Optional[str] = None
    caution_if_below_percentile: Optional[int] = None
    blunted: Optional[str] = None
    excessive: Optional[str] = None

class KPINormRef(BaseModel):
    source: str
    age_adj: bool
    sex_adj: bool

class KPICompute(BaseModel):
    preferred_variant: str
    notes: str

class KPIDefinition(BaseModel):
    name: str
    unit: str
    scope: Optional[str] = None
    description: Optional[str] = None
    range: List[float]
    thresholds: Optional[KPIThresholds] = None
    norm_ref: Optional[KPINormRef] = None
    compute: Optional[KPICompute] = None
    version: str

class KPIRegistry(BaseModel):
    kpis: Dict[str, KPIDefinition]

# --- KPI Bindings Models (The "So What") --------------------------------------

class KPIAction(BaseModel):
    name: str
    params: Optional[Dict[str, Any]] = None

class KPIAlerting(BaseModel):
    risk_if: Optional[str] = None
    caution_if_drop_pct: Optional[str] = None
    actions: List[KPIAction]

class KPIBinding(BaseModel):
    key: str
    role: str
    alerting: KPIAlerting

class CollaborationBinding(BaseModel):
    agent: str
    reason: str

class AgentKPIBindings(BaseModel):
    agent: str
    version: str
    kpis_used: List[KPIBinding]
    collaboration: Dict[str, List[CollaborationBinding]]

# --- Validation Runner --------------------------------------------------------

def validate_configs():
    """
    Loads and validates all KPI-related YAML files.
    This function can be called from a CI/CD pipeline.
    """
    print("🚀 Running KPI Configuration Validation...")
    print("="*40)
    
    # 1. Validate the Canonical KPI Registry
    registry_path = os.path.join(os.path.dirname(__file__), 'shared_modules', 'kpi_registry.yaml')
    print(f"🔍 Validating KPI Registry: {registry_path}")
    try:
        with open(registry_path, 'r') as f:
            registry_data = yaml.safe_load(f)
        registry = KPIRegistry(**registry_data)
        print(f"✅ SUCCESS: KPI Registry is valid. Contains {len(registry.kpis)} KPIs.")
    except Exception as e:
        print(f"❌ ERROR: KPI Registry validation failed!")
        print(e)
        return False

    # 2. Validate Agent-Specific KPI Bindings
    print("\n🔍 Validating Agent KPI Bindings...")
    agents_dir = os.path.dirname(__file__)
    binding_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(agents_dir)
        for file in files
        if file == 'kpi_bindings.yaml'
    ]

    all_bindings_valid = True
    for path in binding_files:
        print(f"  - Validating: {path}")
        try:
            with open(path, 'r') as f:
                binding_data = yaml.safe_load(f)
            bindings = AgentKPIBindings(**binding_data)
            
            # Cross-reference check: ensure all bound KPIs exist in the registry
            for kpi in bindings.kpis_used:
                if kpi.key not in registry.kpis:
                    raise ValueError(f"KPI '{kpi.key}' in '{path}' is not defined in the canonical registry!")

            print(f"    ✅ SUCCESS: Bindings for '{bindings.agent}' are valid.")
        except Exception as e:
            print(f"    ❌ ERROR: Binding validation failed for {path}!")
            print(f"      {e}")
            all_bindings_valid = False

    if all_bindings_valid:
        print("\n✅ SUCCESS: All agent bindings are valid.")
    else:
        print("\n❌ ERROR: One or more agent binding files are invalid.")
        return False
        
    print("\n🎉 All KPI configurations are valid and consistent!")
    return True

if __name__ == "__main__":
    if not validate_configs():
        exit(1) 