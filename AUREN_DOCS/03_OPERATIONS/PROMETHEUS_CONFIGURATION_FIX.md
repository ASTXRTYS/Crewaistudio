# PROMETHEUS CONFIGURATION FIX
## Fixing Metrics Collection Issues

*Created: July 28, 2025*  
*Author: Senior Engineer*  
*Purpose: Document and fix Prometheus target configuration*

---

## 🚨 ISSUE SUMMARY

**Problem**: Grafana shows no activity because:
1. Biometric API `/metrics` endpoint returns JSON instead of Prometheus format
2. Exporters can't be reached via external IP from within Docker network
3. Prometheus shows all targets as "down" except itself

**Status**:
- ✅ Exporters are running and accessible locally
- ❌ Prometheus can't reach them due to network configuration
- ❌ Biometric API metrics not implemented properly

---

## 🔧 CONFIGURATION FIX

### Current (Broken) Configuration:
```yaml
# Uses external IP which doesn't work from container
- job_name: 'node-exporter'
  static_configs:
    - targets: ['144.126.215.218:9100']
```

### Fixed Configuration:
```yaml
# Use Docker container names on internal network
- job_name: 'node-exporter'
  static_configs:
    - targets: ['auren-node-exporter:9100']
```

---

## 📝 COMPLETE FIXED prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'biometric-api'
    static_configs:
      - targets: ['biometric-production:8888']
    metrics_path: '/metrics'

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['auren-redis-exporter:9121']

  - job_name: 'postgres-exporter'  
    static_configs:
      - targets: ['auren-postgres-exporter:9187']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['auren-node-exporter:9100']
```

---

## 🚀 IMPLEMENTATION STEPS

### 1. Update Prometheus Config
```bash
# Create fixed config
cat > /tmp/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'biometric-api'
    static_configs:
      - targets: ['biometric-production:8888']
    metrics_path: '/metrics'

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['auren-redis-exporter:9121']

  - job_name: 'postgres-exporter'  
    static_configs:
      - targets: ['auren-postgres-exporter:9187']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['auren-node-exporter:9100']
EOF

# Copy to container
docker cp /tmp/prometheus.yml auren-prometheus:/etc/prometheus/prometheus.yml

# Reload
docker kill -s HUP auren-prometheus
```

### 2. Fix Biometric API Metrics
The `/metrics` endpoint needs to:
1. Import prometheus_client
2. Return metrics in Prometheus text format
3. Include custom metrics for:
   - Webhook events processed
   - Memory tier operations
   - NEUROS mode transitions
   - Processing latencies

---

## ✅ VERIFICATION

After applying fix:
```bash
# Check targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# All should show "health": "up" except biometric-api (until metrics implemented)
```

---

## 📊 EXPECTED GRAFANA DASHBOARDS

Once fixed, these will show data:
1. **System Metrics** - CPU, memory, disk (from node-exporter)
2. **PostgreSQL Metrics** - Connections, queries, performance
3. **Redis Metrics** - Commands, memory, connections
4. **AUREN Metrics** - Webhook events, processing times (needs implementation)

---

*This fix will enable proper metrics collection in Grafana.* 