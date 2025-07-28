# PERFORMANCE BASELINE & BENCHMARKING GUIDE

**Version**: 1.0  
**Last Updated**: January 20, 2025  
**Author**: AUREN Performance Team  
**Review Cycle**: Monthly  

---

## 📊 Executive Summary

This document establishes performance baselines for AUREN infrastructure and provides benchmarking procedures to ensure optimal system performance.

**Current Performance Targets:**
- **API Response Time**: < 200ms (p95)
- **Page Load Time**: < 2 seconds
- **Concurrent Users**: 100-500
- **Database Query Time**: < 50ms (p95)

---

## 🎯 Current Performance Metrics

### System Baselines (As of January 2025)

#### Response Times
| Endpoint | Average | P50 | P95 | P99 |
|----------|---------|-----|-----|-----|
| `/` (Homepage) | 45ms | 40ms | 85ms | 120ms |
| `/api/health` | 12ms | 10ms | 25ms | 40ms |
| `/api/memory/stats` | 65ms | 55ms | 120ms | 180ms |
| `/api/knowledge-graph/data` | 180ms | 150ms | 350ms | 500ms |
| `/api/biometric/analyze` | 250ms | 200ms | 450ms | 800ms |

#### Resource Utilization
| Resource | Idle | Normal | Peak | Limit |
|----------|------|--------|------|-------|
| CPU (Overall) | 15% | 35% | 65% | 80% |
| Memory | 2.1GB | 2.8GB | 3.5GB | 4.0GB |
| Disk I/O | 5MB/s | 15MB/s | 40MB/s | 100MB/s |
| Network In | 1MB/s | 5MB/s | 20MB/s | 100MB/s |
| Network Out | 2MB/s | 10MB/s | 40MB/s | 100MB/s |

#### Service-Specific Metrics
| Service | CPU | Memory | Requests/sec |
|---------|-----|--------|--------------|
| PostgreSQL | 20% | 800MB | 50-200 |
| Redis | 5% | 200MB | 500-2000 |
| ChromaDB | 15% | 600MB | 10-50 |
| AUREN API | 25% | 400MB | 20-100 |
| Nginx | 5% | 100MB | 100-500 |
| Kafka | 20% | 800MB | 100-1000 |

---

## 🔧 Benchmarking Tools

### 1. API Performance Testing

#### Using Apache Bench (ab)
```bash
# Basic endpoint test
ab -n 1000 -c 10 http://aupex.ai/api/health

# With authentication
ab -n 100 -c 5 -H "Authorization: Bearer YOUR_TOKEN" http://aupex.ai/api/memory/stats

# POST request test
ab -n 100 -c 10 -p payload.json -T application/json http://aupex.ai/api/biometric/analyze
```

#### Using wrk
```bash
# Install wrk
apt install wrk -y

# 30 second test with 12 threads, 400 connections
wrk -t12 -c400 -d30s http://aupex.ai/api/health

# With custom script
wrk -t4 -c100 -d60s -s script.lua http://aupex.ai/api
```

#### Using k6 (Advanced)
```javascript
// k6_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up
    { duration: '5m', target: 100 }, // Stay at 100
    { duration: '2m', target: 0 },   // Ramp down
  ],
};

export default function() {
  let response = http.get('http://aupex.ai/api/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
  sleep(1);
}
```

### 2. Database Performance Testing

#### Query Performance
```sql
-- Enable query timing
\timing on

-- Test common queries
EXPLAIN ANALYZE SELECT * FROM agent_memories WHERE agent_id = 'test' LIMIT 100;
EXPLAIN ANALYZE SELECT COUNT(*) FROM events;
EXPLAIN ANALYZE SELECT * FROM biometric_events WHERE timestamp > NOW() - INTERVAL '1 hour';

-- Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

#### Connection Pool Testing
```bash
# Test connection handling
pgbench -i -s 10 auren_db
pgbench -c 20 -j 4 -t 1000 auren_db

# Monitor connections
watch -n 1 'psql -U auren_user -d auren_db -c "SELECT count(*) FROM pg_stat_activity;"'
```

### 3. Redis Performance Testing

```bash
# Redis benchmark
docker exec auren-redis redis-benchmark -q -n 100000

# Specific operations
docker exec auren-redis redis-benchmark -t set,get -n 100000 -q

# Monitor Redis
docker exec auren-redis redis-cli --stat
```

### 4. System Performance Monitoring

#### Real-time Monitoring Script
```bash
#!/bin/bash
# save as monitor_performance.sh

while true; do
  clear
  echo "=== AUREN Performance Monitor ==="
  echo "Time: $(date)"
  echo ""
  
  echo "=== Docker Stats ==="
  docker stats --no-stream
  
  echo -e "\n=== System Resources ==="
  echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
  echo "Memory: $(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}')"
  echo "Disk: $(df -h / | awk 'NR==2{print $5}')"
  
  echo -e "\n=== Network Connections ==="
  netstat -an | grep ESTABLISHED | wc -l
  
  echo -e "\n=== API Response Time ==="
  curl -o /dev/null -s -w "Connect: %{time_connect}s\nTotal: %{time_total}s\n" http://localhost:8080/health
  
  sleep 5
done
```

---

## 📈 Load Testing Procedures

### 1. Baseline Test (Normal Load)
```bash
# Simulate 50 concurrent users for 5 minutes
wrk -t4 -c50 -d5m --latency http://aupex.ai/api/health

# Expected results:
# - Response time: < 100ms avg
# - Error rate: < 0.1%
# - CPU usage: < 40%
```

### 2. Stress Test (Peak Load)
```bash
# Simulate 200 concurrent users for 10 minutes
wrk -t8 -c200 -d10m --latency http://aupex.ai/api/health

# Expected results:
# - Response time: < 500ms avg
# - Error rate: < 1%
# - CPU usage: < 70%
```

### 3. Spike Test
```bash
# Sudden traffic spike
k6 run --vus 10 --duration 30s spike_test.js
k6 run --vus 500 --duration 30s spike_test.js
k6 run --vus 10 --duration 30s spike_test.js

# Monitor recovery time
```

### 4. Endurance Test
```bash
# Run for extended period
wrk -t4 -c100 -d1h --latency http://aupex.ai/api/health

# Monitor for:
# - Memory leaks
# - Performance degradation
# - Resource exhaustion
```

---

## 🎯 Performance Bottlenecks

### Identified Bottlenecks

#### 1. Database Connection Pool
- **Issue**: Limited connections under high load
- **Current**: 20 connections
- **Recommended**: 50 connections
- **Fix**: Update PostgreSQL max_connections

#### 2. API Worker Threads
- **Issue**: Single-threaded bottleneck
- **Current**: 1 worker
- **Recommended**: 4 workers (2x CPU cores)
- **Fix**: Use gunicorn with multiple workers

#### 3. Redis Memory Limit
- **Issue**: Evictions under load
- **Current**: No limit
- **Recommended**: 1GB limit with LRU
- **Fix**: Set maxmemory in Redis config

#### 4. Nginx Buffer Size
- **Issue**: Large requests failing
- **Current**: Default buffers
- **Recommended**: Increase client_body_buffer_size
- **Fix**: Update nginx.conf

---

## 📊 Monitoring Dashboard

### Prometheus Metrics to Track
```yaml
# Key metrics for alerting
- name: API Response Time
  query: histogram_quantile(0.95, http_request_duration_seconds_bucket)
  threshold: 0.5s

- name: Error Rate
  query: rate(http_requests_total{status=~"5.."}[5m])
  threshold: 0.01

- name: CPU Usage
  query: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
  threshold: 80

- name: Memory Usage
  query: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100
  threshold: 85

- name: Disk Usage
  query: 100 - (node_filesystem_avail_bytes / node_filesystem_size_bytes * 100)
  threshold: 80
```

### Grafana Dashboard Panels
1. **Response Time Heatmap**
2. **Request Rate Graph**
3. **Error Rate Timeline**
4. **Resource Usage Gauges**
5. **Service Health Status**
6. **Database Query Performance**
7. **Cache Hit Ratio**
8. **Network Traffic Flow**

---

## 🚀 Performance Optimization History

### Completed Optimizations

#### January 2025
1. **Added Redis Caching**
   - Result: 60% reduction in database queries
   - Response time improvement: 40%

2. **Enabled Nginx Gzip**
   - Result: 70% reduction in bandwidth
   - Page load improvement: 30%

3. **Database Index Optimization**
   - Result: 80% faster queries
   - Added indexes on frequently queried columns

### Planned Optimizations

#### Q1 2025
1. **CDN Implementation**
   - Expected: 50% faster static assets
   - Global edge caching

2. **Database Connection Pooling**
   - Expected: 30% better connection handling
   - Reduced connection overhead

3. **API Response Caching**
   - Expected: 70% cache hit rate
   - Sub-10ms cached responses

---

## 📈 Capacity Planning

### Current Capacity
| Metric | Current | Maximum | Headroom |
|--------|---------|---------|----------|
| Concurrent Users | 50 | 200 | 150 |
| Requests/Second | 100 | 400 | 300 |
| Database Connections | 20 | 100 | 80 |
| Memory Usage | 2.8GB | 4.0GB | 1.2GB |

### Growth Projections
| Period | Users | RPS | Action Required |
|--------|-------|-----|-----------------|
| Current | 50 | 100 | None |
| 3 months | 200 | 400 | Add Redis replicas |
| 6 months | 500 | 1000 | Upgrade to 8GB RAM |
| 12 months | 1000 | 2000 | Horizontal scaling |

### Scaling Triggers
1. **CPU > 70%** for 10 minutes → Add API workers
2. **Memory > 85%** → Upgrade droplet
3. **Response time > 500ms** (p95) → Investigate bottleneck
4. **Error rate > 1%** → Emergency scaling

---

## 🛠️ Performance Testing Checklist

### Before Load Test
- [ ] Backup database
- [ ] Clear caches
- [ ] Restart services
- [ ] Enable monitoring
- [ ] Notify team

### During Load Test
- [ ] Monitor error logs
- [ ] Watch resource usage
- [ ] Check response times
- [ ] Note anomalies
- [ ] Capture metrics

### After Load Test
- [ ] Analyze results
- [ ] Document findings
- [ ] Plan optimizations
- [ ] Update baselines
- [ ] Share report

---

## 📝 Performance Report Template

```markdown
## Performance Test Report - [DATE]

### Test Configuration
- **Type**: [Baseline/Stress/Spike/Endurance]
- **Duration**: [X minutes]
- **Concurrent Users**: [X]
- **Total Requests**: [X]

### Results Summary
- **Average Response Time**: [X ms]
- **95th Percentile**: [X ms]
- **Error Rate**: [X%]
- **Requests/Second**: [X]

### Resource Usage
- **Peak CPU**: [X%]
- **Peak Memory**: [X GB]
- **Peak Network**: [X Mbps]

### Findings
1. [Finding 1]
2. [Finding 2]

### Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

**Tested By**: [Name]
**Reviewed By**: [Name]
```

---

## 🎯 Quick Performance Wins

### Immediate Improvements
1. **Enable HTTP/2** in Nginx
2. **Add browser caching headers**
3. **Optimize images (WebP format)**
4. **Enable Redis persistence**
5. **Add API response compression**

### Configuration Tweaks
```nginx
# Nginx performance settings
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 100;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript;
}
```

---

*Regular performance testing and optimization ensure AUREN maintains excellent user experience as it scales.* 