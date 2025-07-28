#!/usr/bin/env python3
"""
Create Grafana dashboards for AUREN observability
"""

import requests
import json

GRAFANA_URL = "http://144.126.215.218:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "auren_grafana_2025"

# Memory Tier Dashboard
memory_tier_dashboard = {
    "dashboard": {
        "title": "AUREN AI Agent Memory Tier Visualization",
        "description": "Real-time visualization of how NEUROS manages knowledge across memory tiers",
        "tags": ["ai", "memory", "neuros", "auren"],
        "timezone": "browser",
        "panels": [
            {
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "id": 1,
                "title": "Webhook Requests by Device",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(auren_webhooks_total[5m])",
                        "legendFormat": "{{device_type}}",
                        "refId": "A"
                    }
                ],
                "yaxes": [
                    {"label": "Requests/sec", "show": True},
                    {"show": True}
                ]
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "id": 2,
                "title": "Webhook Processing Duration",
                "type": "graph",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(auren_webhook_duration_seconds_bucket[5m]))",
                        "legendFormat": "p95 {{device_type}}",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
                "id": 3,
                "title": "Biometric Events by Type",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(auren_biometric_events_total[5m])",
                        "legendFormat": "{{device_type}} - {{event_type}}",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                "id": 4,
                "title": "System Metrics",
                "type": "stat",
                "targets": [
                    {
                        "expr": "up{job=\"biometric-api\"}",
                        "legendFormat": "API Status",
                        "refId": "A"
                    }
                ],
                "options": {
                    "colorMode": "value",
                    "graphMode": "none",
                    "justifyMode": "center",
                    "orientation": "auto",
                    "reduceOptions": {
                        "calcs": ["lastNotNull"],
                        "fields": "",
                        "values": False
                    },
                    "textMode": "value"
                },
                "fieldConfig": {
                    "defaults": {
                        "mappings": [
                            {
                                "options": {
                                    "0": {"color": "red", "index": 1, "text": "DOWN"},
                                    "1": {"color": "green", "index": 0, "text": "UP"}
                                },
                                "type": "value"
                            }
                        ],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "red", "value": None},
                                {"color": "green", "value": 1}
                            ]
                        }
                    }
                }
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                "id": 5,
                "title": "Python Memory Usage",
                "type": "gauge",
                "targets": [
                    {
                        "expr": "process_resident_memory_bytes{job=\"biometric-api\"} / 1024 / 1024",
                        "legendFormat": "Memory MB",
                        "refId": "A"
                    }
                ],
                "options": {
                    "showThresholdLabels": False,
                    "showThresholdMarkers": True
                },
                "fieldConfig": {
                    "defaults": {
                        "max": 1000,
                        "min": 0,
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 500},
                                {"color": "red", "value": 800}
                            ]
                        },
                        "unit": "decmbytes"
                    }
                }
            }
        ],
        "refresh": "5s",
        "time": {"from": "now-1h", "to": "now"},
        "uid": "auren-memory-tiers",
        "version": 1
    },
    "overwrite": True
}

# System Overview Dashboard
system_overview_dashboard = {
    "dashboard": {
        "title": "AUREN System Overview",
        "tags": ["auren", "system"],
        "timezone": "browser",
        "panels": [
            {
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 0},
                "id": 1,
                "title": "Service Health Status",
                "type": "table",
                "targets": [
                    {
                        "expr": "up",
                        "format": "table",
                        "instant": True,
                        "refId": "A"
                    }
                ],
                "options": {
                    "showHeader": True
                },
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "align": "auto",
                            "displayMode": "color-background",
                            "filterable": False
                        },
                        "mappings": [
                            {
                                "options": {
                                    "0": {"color": "red", "index": 1, "text": "DOWN"},
                                    "1": {"color": "green", "index": 0, "text": "UP"}
                                },
                                "type": "value"
                            }
                        ]
                    }
                }
            }
        ],
        "refresh": "10s",
        "time": {"from": "now-5m", "to": "now"},
        "uid": "auren-system-overview"
    },
    "overwrite": True
}

def create_dashboard(dashboard_json, auth):
    """Create or update a dashboard in Grafana"""
    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        json=dashboard_json,
        auth=auth
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Dashboard created: {dashboard_json['dashboard']['title']}")
        print(f"   URL: {GRAFANA_URL}{result['url']}")
        return True
    else:
        print(f"❌ Failed to create dashboard: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def main():
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    print("🚀 Creating Grafana dashboards...")
    
    # Create dashboards
    dashboards = [
        memory_tier_dashboard,
        system_overview_dashboard
    ]
    
    success_count = 0
    for dashboard in dashboards:
        if create_dashboard(dashboard, auth):
            success_count += 1
    
    print(f"\n✅ Successfully created {success_count}/{len(dashboards)} dashboards")
    print(f"🎯 Access Grafana at: {GRAFANA_URL}")
    print(f"📊 Login: {GRAFANA_USER} / {GRAFANA_PASS}")

if __name__ == "__main__":
    main() 