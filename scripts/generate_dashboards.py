#!/usr/bin/env python3
"""
Generate Grafana dashboards from KPI Registry
"""
import yaml
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

def map_unit_to_grafana(unit: str) -> str:
    """Map KPI units to Grafana units"""
    unit_mapping = {
        "milliseconds": "ms",
        "ms": "ms",
        "hours": "h",
        "score": "none",
        "bpm": "none",
        "percentage": "percent",
        "count": "none"
    }
    return unit_mapping.get(unit, "none")

def generate_thresholds(thresholds: Dict) -> Dict:
    """Generate Grafana threshold configuration"""
    if not thresholds:
        return {"mode": "absolute", "steps": [{"color": "green", "value": None}]}
    
    steps = []
    
    # Start with green (normal)
    steps.append({"color": "green", "value": None})
    
    # Add warning threshold
    if "warning" in thresholds and "condition" in thresholds["warning"]:
        condition = thresholds["warning"]["condition"]
        if "<" in condition:
            value = float(condition.split("<")[1].strip())
            steps.append({"color": "yellow", "value": value})
        elif ">" in condition:
            value = float(condition.split(">")[1].strip())
            steps.append({"color": "yellow", "value": value})
    
    # Add critical threshold
    if "critical" in thresholds and "condition" in thresholds["critical"]:
        condition = thresholds["critical"]["condition"]
        if "<" in condition:
            value = float(condition.split("<")[1].strip())
            steps.append({"color": "red", "value": value})
        elif ">" in condition:
            value = float(condition.split(">")[1].strip())
            steps.append({"color": "red", "value": value})
    
    return {"mode": "absolute", "steps": sorted(steps, key=lambda x: x["value"] if x["value"] is not None else -1)}

def calculate_grid_position(idx: int, dashboard_config: Dict = None) -> Dict:
    """Calculate panel grid position"""
    if dashboard_config and "position" in dashboard_config:
        return dashboard_config["position"]
    
    # Default 3 panels per row
    row = idx // 3
    col = (idx % 3) * 8
    
    return {
        "x": col,
        "y": row * 8,
        "w": 8,
        "h": 8
    }

def generate_dashboard_from_kpis(kpi_registry_path: str) -> Dict:
    """Generate Grafana dashboard JSON from KPI registry"""
    
    with open(kpi_registry_path) as f:
        registry = yaml.safe_load(f)
    
    panels = []
    for idx, kpi in enumerate(registry['kpis']):
        panel = {
            "datasource": {
                "type": "prometheus",
                "uid": "AUREN-Prometheus"
            },
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "drawStyle": "line",
                        "lineInterpolation": "smooth",
                        "barAlignment": 0,
                        "lineWidth": 2,
                        "fillOpacity": 10,
                        "gradientMode": "opacity",
                        "spanNulls": False,
                        "showPoints": "never",
                        "pointSize": 5,
                        "stacking": {
                            "mode": "none",
                            "group": "A"
                        },
                        "axisPlacement": "auto",
                        "axisLabel": "",
                        "axisColorMode": "text",
                        "scaleDistribution": {
                            "type": "linear"
                        },
                        "axisCenteredZero": False,
                        "hideFrom": {
                            "tooltip": False,
                            "viz": False,
                            "legend": False
                        },
                        "thresholdsStyle": {
                            "mode": "line"
                        }
                    },
                    "mappings": [],
                    "thresholds": generate_thresholds(kpi.get('risk_thresholds', {})),
                    "unit": map_unit_to_grafana(kpi['unit'])
                },
                "overrides": []
            },
            "gridPos": calculate_grid_position(idx, kpi.get('dashboard', {})),
            "id": idx + 1,
            "options": {
                "tooltip": {
                    "mode": "single",
                    "sort": "none"
                },
                "legend": {
                    "showLegend": True,
                    "displayMode": "list",
                    "placement": "bottom",
                    "calcs": []
                }
            },
            "pluginVersion": "10.2.3",
            "targets": [{
                "datasource": {
                    "type": "prometheus",
                    "uid": "AUREN-Prometheus"
                },
                "editorMode": "code",
                "expr": kpi['prometheus_metric'],
                "legendFormat": "{{user_id}}",
                "range": True,
                "refId": "A"
            }],
            "title": f"{kpi.get('category', 'General').upper()}: {kpi['description']}",
            "type": kpi.get('dashboard', {}).get('panel_type', 'timeseries')
        }
        panels.append(panel)
    
    # Add summary stats row
    stats_row = generate_stats_row(registry['kpis'], len(panels))
    panels.extend(stats_row)
    
    return {
        "annotations": {
            "list": [{
                "builtIn": 1,
                "datasource": {
                    "type": "grafana",
                    "uid": "-- Grafana --"
                },
                "enable": True,
                "hide": True,
                "iconColor": "rgba(0, 211, 255, 1)",
                "name": "Annotations & Alerts",
                "type": "dashboard"
            }]
        },
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": panels,
        "refresh": "10s",
        "schemaVersion": 38,
        "tags": ["auren", "kpi", "auto-generated"],
        "templating": {
            "list": [{
                "current": {
                    "selected": False,
                    "text": "All",
                    "value": "$__all"
                },
                "datasource": {
                    "type": "prometheus",
                    "uid": "AUREN-Prometheus"
                },
                "definition": "label_values(user_id)",
                "hide": 0,
                "includeAll": True,
                "label": "User ID",
                "multi": True,
                "name": "user_id",
                "options": [],
                "query": {
                    "query": "label_values(user_id)",
                    "refId": "PrometheusVariableQueryEditor-VariableQuery"
                },
                "refresh": 1,
                "regex": "",
                "skipUrlSync": False,
                "sort": 0,
                "type": "query"
            }]
        },
        "time": {
            "from": "now-6h",
            "to": "now"
        },
        "timepicker": {},
        "timezone": "",
        "title": "AUREN KPIs - Auto-Generated",
        "uid": "auren-kpi-auto",
        "version": 1,
        "weekStart": ""
    }

def generate_stats_row(kpis: List[Dict], start_id: int) -> List[Dict]:
    """Generate a row of stat panels for current values"""
    panels = []
    
    for idx, kpi in enumerate(kpis[:4]):  # Show first 4 KPIs as stats
        panel = {
            "datasource": {
                "type": "prometheus",
                "uid": "AUREN-Prometheus"
            },
            "fieldConfig": {
                "defaults": {
                    "mappings": [],
                    "thresholds": generate_thresholds(kpi.get('risk_thresholds', {})),
                    "unit": map_unit_to_grafana(kpi['unit']),
                    "decimals": 2
                },
                "overrides": []
            },
            "gridPos": {
                "x": idx * 6,
                "y": 0,
                "w": 6,
                "h": 4
            },
            "id": start_id + idx + 1,
            "options": {
                "colorMode": "value",
                "graphMode": "area",
                "justifyMode": "auto",
                "orientation": "auto",
                "reduceOptions": {
                    "values": False,
                    "calcs": ["lastNotNull"],
                    "fields": ""
                },
                "textMode": "auto"
            },
            "pluginVersion": "10.2.3",
            "targets": [{
                "datasource": {
                    "type": "prometheus",
                    "uid": "AUREN-Prometheus"
                },
                "editorMode": "code",
                "expr": f"avg({kpi['prometheus_metric']})",
                "legendFormat": "__auto",
                "range": True,
                "refId": "A"
            }],
            "title": kpi['name'].replace('_', ' ').title(),
            "type": "stat"
        }
        panels.append(panel)
    
    return panels

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Grafana dashboards from KPI registry')
    parser.add_argument('--input', required=True, help='Path to KPI registry YAML')
    parser.add_argument('--output', required=True, help='Output path for dashboard JSON')
    
    args = parser.parse_args()
    
    try:
        dashboard = generate_dashboard_from_kpis(args.input)
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        print(f"✅ Generated dashboard: {output_path}")
        print(f"   Panels: {len(dashboard['panels'])}")
        
    except Exception as e:
        print(f"❌ Error generating dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()