#!/usr/bin/env python3
"""
Validate KPI Registry against schema
"""
import yaml
import jsonschema
import sys
from pathlib import Path

def load_schema():
    """Load the KPI schema"""
    schema = {
        "type": "object",
        "required": ["version", "kpis"],
        "properties": {
            "version": {"type": "string"},
            "last_updated": {"type": "string"},
            "schema_version": {"type": "string"},
            "kpis": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "description", "unit", "prometheus_metric"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "pattern": "^[a-z][a-z0-9_]*$"
                        },
                        "description": {"type": "string"},
                        "unit": {
                            "type": "string",
                            "enum": ["milliseconds", "hours", "score", "bpm", "percentage", "ms", "count"]
                        },
                        "category": {"type": "string"},
                        "prometheus_metric": {
                            "type": "string",
                            "pattern": "^[a-z_][a-z0-9_]*$"
                        },
                        "normal_range": {
                            "type": "object",
                            "properties": {
                                "min": {"type": "number"},
                                "max": {"type": "number"},
                                "optimal": {"type": "number"}
                            }
                        },
                        "risk_thresholds": {
                            "type": "object",
                            "properties": {
                                "critical": {
                                    "type": "object",
                                    "properties": {
                                        "condition": {"type": "string"},
                                        "action": {"type": "string"}
                                    }
                                },
                                "warning": {
                                    "type": "object",
                                    "properties": {
                                        "condition": {"type": "string"},
                                        "action": {"type": "string"}
                                    }
                                },
                                "elevated": {
                                    "type": "object",
                                    "properties": {
                                        "condition": {"type": "string"},
                                        "action": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    return schema

def validate_kpi_registry(registry_path):
    """Validate the KPI registry file"""
    try:
        with open(registry_path, 'r') as f:
            data = yaml.safe_load(f)
        
        schema = load_schema()
        jsonschema.validate(data, schema)
        
        print(f"✅ KPI Registry validation passed!")
        print(f"   Found {len(data['kpis'])} KPIs")
        
        # Additional validation
        metric_names = set()
        for kpi in data['kpis']:
            if kpi['prometheus_metric'] in metric_names:
                print(f"❌ Duplicate metric name: {kpi['prometheus_metric']}")
                return False
            metric_names.add(kpi['prometheus_metric'])
        
        return True
        
    except jsonschema.ValidationError as e:
        print(f"❌ Validation error: {e.message}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    registry_path = Path("agents/shared_modules/kpi_registry.yaml")
    if not registry_path.exists():
        print(f"❌ Registry not found at {registry_path}")
        sys.exit(1)
    
    if validate_kpi_registry(registry_path):
        sys.exit(0)
    else:
        sys.exit(1)