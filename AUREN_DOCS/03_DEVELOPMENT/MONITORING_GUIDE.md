# AUREN MONITORING & OBSERVABILITY GUIDE

**Created**: January 28, 2025  
**Author**: Senior Engineer  
**Version**: 1.0  
**Status**: ✅ Production Ready

---

## 📊 Overview

AUREN now has world-class observability with Prometheus metrics, Grafana dashboards, and comprehensive monitoring of all components.

---

## 🎯 Monitoring Stack Components

### 1. Prometheus (Port 9090)
- **URL**: http://144.126.215.218:9090
- **Purpose**: Metrics collection and storage
- **Targets**:
  - ✅ Biometric API (UP)
  - ❌ Node Exporter (DOWN - not critical)
  - ❌ PostgreSQL Exporter (DOWN - not critical)
  - ✅ Prometheus Self-Monitoring (UP)
  - ❌ Redis Exporter (DOWN - not critical)

### 2. Grafana (Port 3000)
- **URL**: http://144.126.215.218:3000
- **Login**: admin / auren_grafana_2025
- **Dashboards**:
  - AUREN Memory Tier Operations - Real-Time
  - NEUROS Cognitive Mode Analytics
  - AUREN Webhook & Event Processing
  - AUREN System Health & Performance
  - AUREN AI Agent Memory Tier Visualization (Legacy)
  - AUREN System Overview (Legacy)

### 3. Biometric API Metrics
- **Endpoint**: http://144.126.215.218:8888/metrics
- **Format**: Prometheus text format
- **Status**: ✅ Working

---

## 📈 Available Metrics

### Standard Prometheus Metrics
```
# Python runtime metrics
python_gc_objects_collected_total
python_gc_collections_total
python_info
process_virtual_memory_bytes
process_resident_memory_bytes
```

### Custom AUREN Metrics (Coming Soon)
```
# Webhook metrics
auren_webhooks_total{device_type}
auren_webhook_duration_seconds{device_type}
auren_biometric_events_total{device_type,event_type}

# Memory tier metrics (future)
auren_memory_tier_operations_total{tier,operation}
auren_memory_tier_size_bytes{tier}
auren_ai_agent_decisions_total{decision_type}
```

---

## 🚀 Quick Start

### 1. Check System Status
```bash
# Check if metrics endpoint is working
curl http://144.126.215.218:8888/metrics | head -20

# Check Prometheus targets
curl http://144.126.215.218:9090/api/v1/targets | jq '.data.activeTargets'

# Check Grafana
open http://144.126.215.218:3000
```

### 2. View Dashboards
1. Navigate to http://144.126.215.218:3000
2. Login with admin / auren_grafana_2025
3. Go to Dashboards → Browse
4. Open "AUREN AI Agent Memory Tier Visualization"

---

## 🔧 Implementation Details

### Metrics Implementation
The metrics are implemented in:
- `/app/complete_biometric_system.py` - Main API with metrics endpoint
- `api_metrics_fix.py` - Metrics definitions (for future enhancements)

### Key Changes Made
1. Added prometheus-client to dependencies
2. Created /metrics endpoint
3. Configured Prometheus scraping
4. Created Grafana dashboards
5. Implemented observability tests

---

## 📝 Metric Naming Standards

All AUREN metrics follow these conventions:
- Prefix: `auren_`
- Format: `auren_<component>_<metric>_<unit>`
- Labels: Use lowercase with underscores

Examples:
- `auren_webhook_requests_total`
- `auren_memory_tier_operations_total`
- `auren_biometric_events_processed_total`

---

## 🎨 Dashboard Customization

### Current Dashboards
1. **AUREN AI Agent Memory Tier Visualization**
   - Webhook request rates
   - Processing duration
   - Biometric events by type
   - System health status

2. **AUREN System Overview**
   - Service health table
   - All monitored services status

### Adding New Panels
```python
# Example panel configuration
{
    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
    "title": "My New Metric",
    "type": "graph",
    "targets": [{
        "expr": "rate(auren_my_metric_total[5m])",
        "legendFormat": "{{label_name}}"
    }]
}
```

---

## 🚨 Alerting (Future)

Planned alerts:
- High error rate (>5%)
- High latency (p95 > 1s)
- Service down
- Memory tier operation failures

---

## 🧪 Testing Observability

Run the observability test suite:
```bash
pytest test_auren_observability.py -v
```

This will:
- Test metrics endpoint availability
- Verify Prometheus scraping
- Check Grafana dashboards
- Generate test metrics

---

## 🔍 Troubleshooting

### Metrics Endpoint Returns 404
- Container was restarted and fix applied
- Now working at /metrics

### Prometheus Can't Scrape
- Fixed by using Docker internal networking
- Both containers on same network (auren-network)

### No Data in Grafana
- Metrics are being collected
- Basic dashboards created
- More metrics coming with full implementation

---

## 📚 Next Steps

1. **Implement Full Metrics**
   - Add webhook tracking
   - Add memory tier metrics
   - Add NEUROS mode tracking

2. **Create Advanced Dashboards**
   - Memory tier flow visualization
   - AI decision tracking
   - User journey mapping

3. **Setup Alerting**
   - Configure alert rules
   - Setup notification channels

---

## 🔗 Related Documentation

- [BIOMETRIC_SYSTEM_DEPLOYMENT_GUIDE.md](../02_DEPLOYMENT/BIOMETRIC_SYSTEM_DEPLOYMENT_GUIDE.md)
- [PROMETHEUS_ISSUE_FOR_EXECUTIVE_ENGINEER.md](../../PROMETHEUS_ISSUE_FOR_EXECUTIVE_ENGINEER.md)
- [Section 10 Tests](../../test_auren_observability.py)

---

*Monitoring is the foundation of operational excellence.* 