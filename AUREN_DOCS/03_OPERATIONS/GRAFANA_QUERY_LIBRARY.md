# AUREN GRAFANA QUERY LIBRARY

**Created**: January 28, 2025  
**Author**: Senior Engineer  
**Version**: 1.0  
**Purpose**: PromQL queries for AUREN Grafana dashboards

---

## 📊 Query Categories

This library contains tested PromQL queries organized by use case. Copy and paste directly into Grafana panels.

---

## 🎯 Webhook Performance Queries

### Request Rate by Device
```promql
sum by (device_type) (rate(auren_webhook_requests_total[5m]))
```

### Success Rate Percentage
```promql
(sum by (device_type) (rate(auren_webhook_requests_total{status="success"}[5m])) 
/ 
sum by (device_type) (rate(auren_webhook_requests_total[5m]))) * 100
```

### Error Rate by Type
```promql
sum by (device_type, error_type) (rate(auren_webhook_errors_total[5m]))
```

### P95 Latency by Device
```promql
histogram_quantile(0.95, 
  sum by (device_type, le) (
    rate(auren_webhook_request_duration_seconds_bucket[5m])
  )
)
```

### P99 Latency Comparison
```promql
histogram_quantile(0.99, 
  sum by (device_type, le) (
    rate(auren_webhook_request_duration_seconds_bucket[5m])
  )
)
```

### Active Requests (Current Load)
```promql
sum(auren_webhook_active_requests)
```

### Payload Size P95
```promql
histogram_quantile(0.95,
  sum by (device_type, le) (
    rate(auren_webhook_payload_size_bytes_bucket[1h])
  )
)
```

### Request Rate Trend (1h moving average)
```promql
avg_over_time(
  sum by (device_type) (
    rate(auren_webhook_requests_total[5m])
  )[1h:5m]
)
```

---

## 🧠 Memory Tier Queries

### Memory Operations per Second
```promql
sum by (tier, operation) (
  rate(auren_memory_tier_operations_total[5m])
)
```

### Memory Tier Fill Percentage
```promql
(auren_memory_tier_size_bytes / 1073741824) * 100  # Convert to GB percentage
```

### Cache Hit Rate
```promql
auren_memory_tier_hit_rate * 100
```

### Memory Promotion Rate
```promql
sum by (from_tier, to_tier) (
  rate(auren_ai_agent_decisions_total{decision_type="tier_promotion"}[5m])
)
```

### Memory Operation Latency Heatmap
```promql
sum by (tier, le) (
  rate(auren_memory_tier_latency_seconds_bucket[5m])
)
```

### Memory Pressure Indicator
```promql
(auren_memory_tier_size_bytes{tier="hot"} / 268435456) * 100  # 256MB hot tier limit
```

### AI Decision Frequency
```promql
sum by (decision_type, reason) (
  rate(auren_ai_agent_decisions_total[1h])
)
```

### Memory Tier Item Distribution
```promql
auren_memory_tier_items_count
```

---

## 🧠 NEUROS Mode Analytics

### Mode Switch Rate
```promql
sum by (from_mode, to_mode) (
  rate(auren_neuros_mode_switches_total[1h])
)
```

### Current Mode Distribution
```promql
count by (auren_neuros_current_mode) (auren_neuros_current_mode)
```

### Average Time in Mode
```promql
histogram_quantile(0.5, 
  sum by (mode, le) (
    rate(auren_neuros_mode_duration_seconds_bucket[24h])
  )
) / 60  # Convert to minutes
```

### Mode Transition Matrix
```promql
sum by (from_mode, to_mode) (
  increase(auren_neuros_mode_switches_total[24h])
)
```

### Hypothesis Generation Rate
```promql
sum by (category, confidence_level) (
  rate(auren_neuros_hypothesis_generated_total[1h])
)
```

### Pattern Recognition by Type
```promql
sum by (pattern_type) (
  increase(auren_neuros_pattern_recognition_total[24h])
)
```

### High Significance Patterns
```promql
sum by (pattern_type) (
  increase(auren_neuros_pattern_recognition_total{significance="high"}[24h])
)
```

---

## 📈 Biometric Event Queries

### Event Processing Rate
```promql
sum by (device_type, event_type) (
  rate(auren_biometric_events_processed_total[5m])
)
```

### Heart Rate Distribution
```promql
histogram_quantile(0.5,
  sum by (le) (
    rate(auren_biometric_event_values_bucket{metric_type="heart_rate"}[24h])
  )
)
```

### HRV Trends
```promql
histogram_quantile(0.5,
  sum by (device_type, le) (
    rate(auren_biometric_event_values_bucket{metric_type="hrv"}[24h])
  )
)
```

### Data Quality by Device
```promql
avg by (device_type) (auren_biometric_data_quality_score)
```

### Anomaly Detection Rate
```promql
sum by (device_type, anomaly_type, severity) (
  rate(auren_biometric_anomalies_detected_total[1h])
)
```

### Critical Anomalies
```promql
sum by (device_type, anomaly_type) (
  rate(auren_biometric_anomalies_detected_total{severity="high"}[5m])
)
```

---

## 🚀 Kafka Streaming Queries

### Message Throughput
```promql
sum by (topic) (
  rate(auren_kafka_messages_sent_total[5m])
)
```

### Kafka Success Rate
```promql
(sum by (topic) (rate(auren_kafka_messages_sent_total{status="success"}[5m]))
/
sum by (topic) (rate(auren_kafka_messages_sent_total[5m]))) * 100
```

### Kafka Latency P99
```promql
histogram_quantile(0.99,
  sum by (topic, le) (
    rate(auren_kafka_message_send_duration_seconds_bucket[5m])
  )
)
```

### Average Batch Size
```promql
histogram_quantile(0.5,
  sum by (topic, le) (
    rate(auren_kafka_batch_size_bucket[1h])
  )
)
```

---

## 💻 System Health Queries

### Database Connection Usage
```promql
sum by (database) (auren_database_connections_active)
```

### API Endpoint Availability
```promql
min by (endpoint) (auren_api_endpoint_availability)
```

### Python Memory Usage
```promql
process_resident_memory_bytes / 1024 / 1024  # Convert to MB
```

### CPU Usage
```promql
rate(process_cpu_seconds_total[5m]) * 100
```

### Garbage Collection Frequency
```promql
rate(python_gc_collections_total[5m])
```

---

## 📊 Alert Queries

### High Error Rate Alert
```promql
(sum(rate(auren_webhook_errors_total[5m])) 
/ 
sum(rate(auren_webhook_requests_total[5m]))) > 0.05
```

### Memory Tier Latency Alert
```promql
histogram_quantile(0.95, 
  rate(auren_memory_tier_latency_seconds_bucket[5m])
) > 1.0
```

### Low Cache Hit Rate Alert
```promql
auren_memory_tier_hit_rate{tier="hot"} < 0.7
```

### Kafka Backlog Alert
```promql
rate(auren_kafka_messages_sent_total{status="failed"}[5m]) > 0
```

### Database Connection Pool Alert
```promql
auren_database_connections_active / 100 > 0.8  # 80% of pool size
```

---

## 🎨 Dashboard Panel Queries

### Combined Error & Success Rate
```promql
sum by (device_type, status) (
  rate(auren_webhook_requests_total[5m])
)
```

### Stacked Memory Tier Sizes
```promql
auren_memory_tier_size_bytes
```

### Request Latency Percentiles
```promql
histogram_quantile(0.5, sum by (le) (rate(auren_webhook_request_duration_seconds_bucket[5m])))
histogram_quantile(0.95, sum by (le) (rate(auren_webhook_request_duration_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le) (rate(auren_webhook_request_duration_seconds_bucket[5m])))
```

### System Overview Stats
```promql
# Request rate
sum(rate(auren_webhook_requests_total[5m]))

# Error percentage  
(sum(rate(auren_webhook_errors_total[5m])) / sum(rate(auren_webhook_requests_total[5m]))) * 100

# Active connections
sum(auren_database_connections_active)

# Memory usage
process_resident_memory_bytes / 1024 / 1024
```

---

## 🔍 Debugging Queries

### Find Missing Metrics
```promql
up{job="biometric-api"}
```

### Check Metric Cardinality
```promql
count by (__name__)({__name__=~"auren_.*"})
```

### Identify High Cardinality Labels
```promql
count by (device_type) (
  group by (device_type, user_id_hash) (
    auren_biometric_events_processed_total
  )
)
```

### Rate of Change Detection
```promql
deriv(auren_memory_tier_size_bytes[1h])
```

---

## 📝 Query Best Practices

1. **Time Ranges**: Use appropriate time ranges for rate calculations
   - `[5m]` for real-time monitoring
   - `[1h]` for trend analysis
   - `[24h]` for daily patterns

2. **Aggregations**: Always specify aggregation labels
   - Use `sum by (label)` instead of just `sum`
   - Use `avg by (label)` for averages

3. **Performance**: Limit query complexity
   - Avoid regex matches on high-cardinality labels
   - Pre-aggregate in recording rules for expensive queries

4. **Units**: Convert to human-readable units
   - Bytes to MB/GB: `/ 1024 / 1024`
   - Ratios to percentages: `* 100`
   - Seconds to minutes: `/ 60`

---

*This query library is maintained alongside the metrics catalog. Test queries in Grafana Explore before adding to dashboards.* 