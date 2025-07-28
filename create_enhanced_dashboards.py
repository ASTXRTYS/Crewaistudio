#!/usr/bin/env python3
"""
Create enhanced Grafana dashboards for AUREN observability
"""

import requests
import json

GRAFANA_URL = "http://144.126.215.218:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "auren_grafana_2025"

# Enhanced Memory Tier Dashboard
memory_tier_dashboard = {
    "dashboard": {
        "title": "AUREN Memory Tier Operations - Real-Time",
        "description": "Live visualization of AI agent memory tier decisions and data flow",
        "tags": ["memory", "ai", "neuros", "tiers"],
        "timezone": "browser",
        "panels": [
            # Row 1: Memory Tier Flow Overview
            {
                "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0},
                "id": 1,
                "title": "Memory Tier Operations Flow",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(auren_memory_tier_operations_total[5m])",
                        "legendFormat": "{{tier}} - {{operation}} ({{trigger}})",
                        "refId": "A"
                    }
                ],
                "yaxes": [
                    {"label": "Operations/sec", "show": True},
                    {"show": True}
                ]
            },
            {
                "gridPos": {"h": 8, "w": 8, "x": 8, "y": 0},
                "id": 2,
                "title": "AI Agent Decisions",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(auren_ai_agent_decisions_total[5m])",
                        "legendFormat": "{{decision_type}}: {{from_tier}}→{{to_tier}}",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 8, "x": 16, "y": 0},
                "id": 3,
                "title": "Memory Tier Sizes",
                "type": "bargauge",
                "targets": [
                    {
                        "expr": "auren_memory_tier_size_bytes",
                        "legendFormat": "{{tier}}",
                        "refId": "A"
                    }
                ],
                "options": {
                    "displayMode": "gradient",
                    "orientation": "horizontal",
                    "showUnfilled": True
                },
                "fieldConfig": {
                    "defaults": {
                        "unit": "decbytes",
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 1000000},
                                {"color": "red", "value": 10000000}
                            ]
                        }
                    }
                }
            },
            # Row 2: Memory Performance
            {
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "id": 4,
                "title": "Memory Operation Latency Heatmap",
                "type": "heatmap",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(auren_memory_tier_latency_seconds_bucket[5m]))",
                        "legendFormat": "{{tier}} - {{operation}}",
                        "refId": "A"
                    }
                ],
                "options": {
                    "calculate": True,
                    "calculation": {
                        "xBuckets": {"mode": "count", "value": "30"},
                        "yBuckets": {"mode": "count", "value": "10"}
                    },
                    "color": {
                        "mode": "scheme",
                        "scheme": "Spectral",
                        "steps": 128
                    }
                }
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "id": 5,
                "title": "Memory Hit Rates",
                "type": "stat",
                "targets": [
                    {
                        "expr": "auren_memory_tier_hit_rate",
                        "legendFormat": "{{tier}}",
                        "refId": "A"
                    }
                ],
                "options": {
                    "colorMode": "background",
                    "graphMode": "area",
                    "orientation": "horizontal"
                },
                "fieldConfig": {
                    "defaults": {
                        "unit": "percentunit",
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "red", "value": None},
                                {"color": "yellow", "value": 0.7},
                                {"color": "green", "value": 0.85}
                            ]
                        }
                    }
                }
            }
        ],
        "refresh": "5s",
        "time": {"from": "now-30m", "to": "now"},
        "uid": "auren-memory-tiers-enhanced"
    },
    "overwrite": True
}

# NEUROS Cognitive Mode Dashboard
neuros_dashboard = {
    "dashboard": {
        "title": "NEUROS Cognitive Mode Analytics",
        "description": "Real-time tracking of NEUROS mode switches and AI behavior patterns",
        "tags": ["neuros", "ai", "cognitive", "modes"],
        "timezone": "browser",
        "panels": [
            # Row 1: Mode Overview
            {
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "id": 1,
                "title": "NEUROS Mode Transitions",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(auren_neuros_mode_switches_total[5m])",
                        "legendFormat": "{{from_mode}}→{{to_mode}} ({{trigger_type}})",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "id": 2,
                "title": "Current Mode Distribution",
                "type": "piechart",
                "targets": [
                    {
                        "expr": "count by (auren_neuros_current_mode) (auren_neuros_current_mode)",
                        "legendFormat": "{{auren_neuros_current_mode}}",
                        "refId": "A"
                    }
                ]
            },
            # Row 2: Mode Analytics
            {
                "gridPos": {"h": 8, "w": 8, "x": 0, "y": 8},
                "id": 3,
                "title": "Mode Duration Analysis",
                "type": "heatmap",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(auren_neuros_mode_duration_seconds_bucket[1h]))",
                        "legendFormat": "{{mode}}",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 8, "x": 8, "y": 8},
                "id": 4,
                "title": "Hypothesis Generation Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(auren_neuros_hypothesis_generated_total[5m])",
                        "legendFormat": "{{category}} - {{confidence_level}}",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 8, "x": 16, "y": 8},
                "id": 5,
                "title": "Pattern Recognition",
                "type": "bargauge",
                "targets": [
                    {
                        "expr": "increase(auren_neuros_pattern_recognition_total[1h])",
                        "legendFormat": "{{pattern_type}} ({{significance}})",
                        "refId": "A"
                    }
                ],
                "options": {
                    "displayMode": "lcd",
                    "orientation": "horizontal"
                }
            }
        ],
        "refresh": "10s",
        "time": {"from": "now-1h", "to": "now"},
        "uid": "auren-neuros-modes"
    },
    "overwrite": True
}

# Webhook & Event Processing Dashboard
webhook_dashboard = {
    "dashboard": {
        "title": "AUREN Webhook & Event Processing",
        "description": "Real-time webhook processing metrics and biometric event tracking",
        "tags": ["webhooks", "events", "biometric"],
        "timezone": "browser",
        "panels": [
            # Row 1: Webhook Overview
            {
                "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0},
                "id": 1,
                "title": "Webhook Request Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(auren_webhook_requests_total[5m])",
                        "legendFormat": "{{device_type}} - {{event_type}} ({{status}})",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 8, "x": 8, "y": 0},
                "id": 2,
                "title": "Webhook Processing Latency",
                "type": "graph",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(auren_webhook_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "p95 {{device_type}}",
                        "refId": "A"
                    },
                    {
                        "expr": "histogram_quantile(0.99, rate(auren_webhook_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "p99 {{device_type}}",
                        "refId": "B"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 8, "x": 16, "y": 0},
                "id": 3,
                "title": "Active Webhook Requests",
                "type": "gauge",
                "targets": [
                    {
                        "expr": "sum by (device_type) (auren_webhook_active_requests)",
                        "legendFormat": "{{device_type}}",
                        "refId": "A"
                    }
                ],
                "options": {
                    "showThresholdLabels": False,
                    "showThresholdMarkers": True
                },
                "fieldConfig": {
                    "defaults": {
                        "max": 50,
                        "min": 0,
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 20},
                                {"color": "red", "value": 40}
                            ]
                        }
                    }
                }
            },
            # Row 2: Biometric Events
            {
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "id": 4,
                "title": "Biometric Events by Device",
                "type": "timeseries",
                "targets": [
                    {
                        "expr": "rate(auren_biometric_events_processed_total[5m])",
                        "legendFormat": "{{device_type}} - {{event_type}}",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "id": 5,
                "title": "Biometric Data Quality",
                "type": "heatmap",
                "targets": [
                    {
                        "expr": "auren_biometric_data_quality_score",
                        "legendFormat": "{{device_type}}",
                        "refId": "A"
                    }
                ],
                "options": {
                    "color": {
                        "mode": "spectrum",
                        "scheme": "RdYlGn"
                    }
                }
            },
            # Row 3: Payload Analysis
            {
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
                "id": 6,
                "title": "Webhook Payload Size Distribution",
                "type": "heatmap",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(auren_webhook_payload_size_bytes_bucket[5m]))",
                        "legendFormat": "{{device_type}}",
                        "refId": "A"
                    }
                ]
            }
        ],
        "refresh": "5s",
        "time": {"from": "now-15m", "to": "now"},
        "uid": "auren-webhooks-events"
    },
    "overwrite": True
}

# System Health Dashboard
system_health_dashboard = {
    "dashboard": {
        "title": "AUREN System Health & Performance",
        "description": "Overall system health, performance metrics, and infrastructure status",
        "tags": ["system", "health", "infrastructure"],
        "timezone": "browser",
        "panels": [
            # Row 1: System Overview
            {
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "id": 1,
                "title": "API Endpoint Availability",
                "type": "stat",
                "targets": [
                    {
                        "expr": "auren_api_endpoint_availability",
                        "legendFormat": "{{endpoint}} ({{method}})",
                        "refId": "A"
                    }
                ],
                "options": {
                    "colorMode": "background",
                    "graphMode": "none"
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
                        ]
                    }
                }
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "id": 2,
                "title": "Database Connections",
                "type": "graph",
                "targets": [
                    {
                        "expr": "auren_database_connections_active",
                        "legendFormat": "{{database}} - {{pool_name}}",
                        "refId": "A"
                    }
                ]
            },
            # Row 2: Errors and Anomalies
            {
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "id": 3,
                "title": "Error Rates by Type",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(auren_webhook_errors_total[5m])",
                        "legendFormat": "Webhook: {{device_type}} - {{error_type}}",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "id": 4,
                "title": "Biometric Anomalies Detected",
                "type": "timeseries",
                "targets": [
                    {
                        "expr": "increase(auren_biometric_anomalies_detected_total[1h])",
                        "legendFormat": "{{device_type}} - {{anomaly_type}} ({{severity}})",
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "bars",
                            "barAlignment": -1
                        }
                    }
                }
            }
        ],
        "refresh": "10s",
        "time": {"from": "now-1h", "to": "now"},
        "uid": "auren-system-health"
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
    
    print("🚀 Creating Enhanced Grafana Dashboards...")
    print("=" * 50)
    
    # Create all dashboards
    dashboards = [
        ("Memory Tier Operations", memory_tier_dashboard),
        ("NEUROS Cognitive Modes", neuros_dashboard),
        ("Webhook Processing", webhook_dashboard),
        ("System Health", system_health_dashboard)
    ]
    
    success_count = 0
    for name, dashboard in dashboards:
        print(f"\n📊 Creating {name} dashboard...")
        if create_dashboard(dashboard, auth):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Successfully created {success_count}/{len(dashboards)} dashboards")
    print(f"\n🎯 Access Grafana at: {GRAFANA_URL}")
    print(f"📊 Login: {GRAFANA_USER} / {GRAFANA_PASS}")
    print("\n📈 New Dashboards:")
    print("  - Memory Tier Operations: See AI decisions in real-time")
    print("  - NEUROS Cognitive Modes: Track mode switches and patterns")
    print("  - Webhook Processing: Monitor all device integrations")
    print("  - System Health: Overall infrastructure status")

if __name__ == "__main__":
    main() 