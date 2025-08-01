#!/usr/bin/env python3
"""
AUREN KPI Binding Validator
Validates per-agent KPI bindings against the registry
"""

import yaml
import sys
from pathlib import Path
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KPIBindingValidator:
    """Validate agent KPI bindings against the registry"""
    
    def __init__(self, registry_path: str = "shared_modules/kpi_registry.yaml"):
        self.registry_kpis = self.load_registry(registry_path)
        self.validation_errors = []
        
    def load_registry(self, path: str) -> Dict[str, Dict]:
        """Load KPI registry"""
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            kpis = {}
            for kpi in data.get('kpis', []):
                kpis[kpi['name']] = kpi
                
            logger.info(f"Loaded {len(kpis)} KPIs from registry")
            return kpis
            
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            return {}
            
    def validate_binding_file(self, binding_path: str) -> bool:
        """Validate a single KPI binding file"""
        try:
            with open(binding_path, 'r') as f:
                binding_data = yaml.safe_load(f)
                
            if not binding_data:
                self.validation_errors.append(f"{binding_path}: Empty binding file")
                return False
                
            return self.validate_binding(binding_data, binding_path)
            
        except Exception as e:
            self.validation_errors.append(f"{binding_path}: Failed to load - {e}")
            return False
            
    def validate_binding(self, binding: Dict[str, Any], file_path: str) -> bool:
        """Validate a single KPI binding"""
        valid = True
        
        # Required fields
        if 'kpi_used' not in binding:
            self.validation_errors.append(f"{file_path}: Missing 'kpi_used' field")
            valid = False
            
        kpi_name = binding.get('kpi_used')
        if kpi_name and kpi_name not in self.registry_kpis:
            self.validation_errors.append(f"{file_path}: KPI '{kpi_name}' not found in registry")
            valid = False
            
        # Thresholds validation
        thresholds = binding.get('thresholds', {})
        if not thresholds:
            self.validation_errors.append(f"{file_path}: Missing 'thresholds' section")
            valid = False
        elif 'risk_if' not in thresholds:
            self.validation_errors.append(f"{file_path}: Missing 'risk_if' condition in thresholds")
            valid = False
            
        # Actions validation
        actions = binding.get('actions', [])
        if not actions:
            self.validation_errors.append(f"{file_path}: Missing 'actions' section")
            valid = False
        else:
            for action in actions:
                if 'name' not in action:
                    self.validation_errors.append(f"{file_path}: Action missing 'name' field")
                    valid = False
                    
        # Agent-specific validation
        agent_name = Path(file_path).parent.name.replace('_modules', '')
        if 'agent' not in binding:
            binding['agent'] = agent_name
            
        if valid:
            logger.info(f"✅ {file_path}: KPI binding valid")
        else:
            logger.error(f"❌ {file_path}: KPI binding invalid")
            
        return valid
        
    def validate_all_bindings(self) -> bool:
        """Validate all agent KPI bindings"""
        binding_files = list(Path('.').glob('*/kpi_bindings.yaml'))
        
        if not binding_files:
            logger.warning("No KPI binding files found")
            return True
            
        all_valid = True
        for binding_file in binding_files:
            if not self.validate_binding_file(str(binding_file)):
                all_valid = False
                
        if self.validation_errors:
            logger.error("KPI Binding validation errors:")
            for error in self.validation_errors:
                logger.error(f"  - {error}")
                
        return all_valid
        
    def generate_binding_template(self, agent_name: str, kpi_name: str) -> Dict[str, Any]:
        """Generate a template KPI binding"""
        if kpi_name not in self.registry_kpis:
            raise ValueError(f"KPI '{kpi_name}' not found in registry")
            
        kpi_def = self.registry_kpis[kpi_name]
        
        template = {
            'agent': agent_name,
            'kpi_used': kpi_name,
            'description': f"{agent_name} monitoring of {kpi_def['description']}",
            'thresholds': {
                'risk_if': '< threshold_value',  # User must customize
                'warning_if': '< warning_value'  # Optional
            },
            'actions': [
                {
                    'name': f'adjust_{agent_name}_recommendations',
                    'description': 'Adjust agent recommendations based on KPI state'
                }
            ],
            'monitoring': {
                'frequency': 'daily',
                'alert_channels': ['dashboard', 'log']
            }
        }
        
        return template

if __name__ == "__main__":
    validator = KPIBindingValidator()
    
    # Validate existing bindings
    if validator.validate_all_bindings():
        print("✅ All KPI bindings are valid")
        sys.exit(0)
    else:
        print("❌ KPI binding validation failed")
        sys.exit(1) 