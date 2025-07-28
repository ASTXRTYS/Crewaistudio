# AUREN MONITORING QUICK START GUIDE
## Your Observability Tools Are Live! 🎉

### 🌐 Access Your Dashboards

**Grafana (Visualization)**: http://144.126.215.218:3000
- Username: `admin`
- Password: `auren_grafana_2025`

**Prometheus (Metrics)**: http://144.126.215.218:9090
- No authentication required
- Query interface for raw metrics

---

## 🚀 Getting Started with Grafana

### 1. First Login
1. Go to http://144.126.215.218:3000
2. Login with admin/auren_grafana_2025
3. You'll see the Grafana home dashboard

### 2. Create Your First Dashboard
1. Click "+" → "Create" → "Dashboard"
2. Click "Add visualization"
3. Select "Prometheus" as data source (already configured)
4. Try these example queries:

#### System Health
```promql
# CPU Usage
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory Usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk Usage
100 - ((node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100)
```

#### PostgreSQL Metrics
```promql
# Active connections
pg_stat_database_numbackends{datname="auren_production"}

# Database size
pg_database_size_bytes{datname="auren_production"}
```

#### Redis Metrics
```promql
# Connected clients
redis_connected_clients

# Used memory
redis_memory_used_bytes

# Commands per second
rate(redis_commands_processed_total[1m])
```

### 3. Recommended Dashboards to Import

1. **Node Exporter Full** (ID: 1860)
   - Complete system metrics
   - CPU, Memory, Disk, Network

2. **PostgreSQL Database** (ID: 9628)
   - Database performance
   - Query stats, connections

3. **Redis Dashboard** (ID: 763)
   - Cache performance
   - Hit/miss ratios

To import: Dashboard → Import → Enter ID → Load

---

## 🔍 Quick Prometheus Queries

Access Prometheus directly at http://144.126.215.218:9090

### Useful Queries:

**See all available metrics:**
```
up
```

**Check service health:**
```
up{job="biometric-api"}
up{job="postgres"}
up{job="redis"}
```

**System load:**
```
node_load1
```

**Free disk space:**
```
node_filesystem_free_bytes{mountpoint="/"}
```

---

## 📊 What's Being Monitored

### System Metrics (Node Exporter)
- CPU usage, load averages
- Memory usage, swap
- Disk I/O, space
- Network traffic

### PostgreSQL Metrics
- Active connections
- Database sizes
- Transaction rates
- Lock statistics

### Redis Metrics
- Memory usage
- Cache hit/miss ratios
- Commands per second
- Connected clients

### Biometric API
- Health endpoint status
- Response times (when instrumented)

---

## 🎯 Next Steps

1. **Create Custom Dashboards**
   - Biometric event processing rate
   - API response times
   - Kafka message throughput

2. **Set Up Alerts**
   - High CPU/Memory usage
   - Database connection limits
   - Service downtime

3. **Add Application Metrics**
   - Instrument biometric API with Prometheus client
   - Export custom business metrics
   - Track user activity patterns

---

## 🆘 Troubleshooting

**Can't access Grafana?**
```bash
# Check if running
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker ps | grep grafana'

# Check logs
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker logs --tail 50 auren-grafana'
```

**Prometheus not collecting metrics?**
```bash
# Check targets
curl http://144.126.215.218:9090/api/v1/targets
```

**Need to restart services?**
```bash
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker restart auren-prometheus auren-grafana'
```

---

## 📈 Sample Dashboard JSON

Here's a starter dashboard for AUREN system health. Import this JSON in Grafana:

```json
{
  "dashboard": {
    "title": "AUREN System Health",
    "panels": [
      {
        "title": "CPU Usage",
        "targets": [
          {
            "expr": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"
          }
        ]
      },
      {
        "title": "PostgreSQL Connections",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends{datname=\"auren_production\"}"
          }
        ]
      },
      {
        "title": "Redis Memory",
        "targets": [
          {
            "expr": "redis_memory_used_bytes / 1024 / 1024"
          }
        ]
      }
    ]
  }
}
```

---

*Your observability stack is now live! Start exploring your metrics and building insights into AUREN's performance.* 🚀 