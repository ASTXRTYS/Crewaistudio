# AUREN METRICS CATALOG

**Created**: January 28, 2025  
**Author**: Senior Engineer  
**Version**: 1.0  
**Purpose**: Complete catalog of all AUREN Prometheus metrics

---

## 📊 Metrics Overview

AUREN uses Prometheus for comprehensive system observability. All custom metrics follow the `auren_` prefix convention for easy identification.

---

## 🎯 Core Application Metrics

### Webhook Metrics

#### `auren_webhook_requests_total`
- **Type**: Counter
- **Description**: Total number of webhook requests received
- **Labels**: 
  - `device_type`: oura, whoop, healthkit
  - `event_type`: sleep, activity, readiness, etc.
  - `status`: success, error
- **Use Case**: Track webhook volume and success rates
- **Example Query**: `rate(auren_webhook_requests_total[5m])`

#### `auren_webhook_request_duration_seconds`
- **Type**: Histogram
- **Description**: Webhook request processing duration
- **Labels**: 
  - `device_type`: oura, whoop, healthkit
  - `method`: POST
- **Buckets**: 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0
- **Use Case**: Monitor processing latency
- **Example Query**: `histogram_quantile(0.95, rate(auren_webhook_request_duration_seconds_bucket[5m]))`

#### `auren_webhook_errors_total`
- **Type**: Counter
- **Description**: Total webhook processing errors
- **Labels**: 
  - `device_type`: oura, whoop, healthkit
  - `error_type`: validation_error, timeout, internal_error
- **Use Case**: Track error patterns
- **Example Query**: `sum by (error_type) (rate(auren_webhook_errors_total[5m]))`

#### `auren_webhook_active_requests`
- **Type**: Gauge
- **Description**: Currently processing webhook requests
- **Labels**: 
  - `device_type`: oura, whoop, healthkit
- **Use Case**: Monitor concurrent load
- **Example Query**: `sum(auren_webhook_active_requests)`

#### `auren_webhook_payload_size_bytes`
- **Type**: Histogram
- **Description**: Size of webhook payloads
- **Labels**: 
  - `device_type`: oura, whoop, healthkit
- **Buckets**: 100, 500, 1000, 5000, 10000, 50000, 100000
- **Use Case**: Monitor payload sizes for capacity planning
- **Example Query**: `histogram_quantile(0.95, rate(auren_webhook_payload_size_bytes_bucket[1h]))`

---

## 🧠 Memory Tier Metrics

### Memory Operations

#### `auren_memory_tier_operations_total`
- **Type**: Counter
- **Description**: Total memory tier operations
- **Labels**: 
  - `tier`: hot, warm, cold
  - `operation`: read, write, promote, archive
  - `trigger`: manual, frequency_threshold, age_threshold
  - `success`: true, false
- **Use Case**: Track memory tier usage patterns
- **Example Query**: `sum by (tier, operation) (rate(auren_memory_tier_operations_total[5m]))`

#### `auren_memory_tier_size_bytes`
- **Type**: Gauge
- **Description**: Current size of each memory tier
- **Labels**: 
  - `tier`: hot, warm, cold
- **Use Case**: Monitor memory usage
- **Example Query**: `auren_memory_tier_size_bytes`

#### `auren_memory_tier_items_count`
- **Type**: Gauge
- **Description**: Number of items in each tier
- **Labels**: 
  - `tier`: hot, warm, cold
- **Use Case**: Track item distribution
- **Example Query**: `auren_memory_tier_items_count`

#### `auren_memory_tier_latency_seconds`
- **Type**: Histogram
- **Description**: Operation latency by tier
- **Labels**: 
  - `tier`: hot, warm, cold
  - `operation`: read, write, promote, archive
- **Buckets**: 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.5
- **Use Case**: Monitor performance by tier
- **Example Query**: `histogram_quantile(0.95, rate(auren_memory_tier_latency_seconds_bucket[5m]))`

#### `auren_memory_tier_hit_rate`
- **Type**: Gauge
- **Description**: Cache hit rate for memory tiers
- **Labels**: 
  - `tier`: hot, warm
- **Use Case**: Monitor cache effectiveness
- **Example Query**: `auren_memory_tier_hit_rate`

### AI Agent Decisions

#### `auren_ai_agent_decisions_total`
- **Type**: Counter
- **Description**: AI agent memory management decisions
- **Labels**: 
  - `decision_type`: tier_promotion, tier_demotion, archival
  - `from_tier`: hot, warm, cold
  - `to_tier`: hot, warm, cold
  - `reason`: frequency, age, space_pressure
- **Use Case**: Track AI decision patterns
- **Example Query**: `sum by (decision_type) (rate(auren_ai_agent_decisions_total[1h]))`

#### `auren_memory_promotion_duration_seconds`
- **Type**: Histogram
- **Description**: Time to promote data between tiers
- **Labels**: 
  - `from_tier`: warm, cold
  - `to_tier`: hot, warm
- **Buckets**: 0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0
- **Use Case**: Monitor promotion performance
- **Example Query**: `histogram_quantile(0.99, rate(auren_memory_promotion_duration_seconds_bucket[5m]))`

---

## 🧠 NEUROS Cognitive Mode Metrics

### Mode Tracking

#### `auren_neuros_mode_switches_total`
- **Type**: Counter
- **Description**: NEUROS cognitive mode transitions
- **Labels**: 
  - `from_mode`: baseline, reflex, hypothesis, pattern, companion, sentinel
  - `to_mode`: baseline, reflex, hypothesis, pattern, companion, sentinel
  - `trigger_type`: manual, threshold, pattern_detection
  - `user_id_hash`: Hashed user ID
- **Use Case**: Track mode switch patterns
- **Example Query**: `sum by (to_mode) (increase(auren_neuros_mode_switches_total[1h]))`

#### `auren_neuros_current_mode`
- **Type**: Enum
- **Description**: Current NEUROS mode per user
- **Labels**: 
  - `user_id_hash`: Hashed user ID
- **States**: baseline, reflex, hypothesis, pattern, companion, sentinel
- **Use Case**: Monitor current mode distribution
- **Example Query**: `count by (auren_neuros_current_mode) (auren_neuros_current_mode)`

#### `auren_neuros_mode_duration_seconds`
- **Type**: Histogram
- **Description**: Time spent in each mode
- **Labels**: 
  - `mode`: baseline, reflex, hypothesis, pattern, companion, sentinel
  - `user_id_hash`: Hashed user ID
- **Buckets**: 60, 300, 600, 1800, 3600, 7200, 14400, 28800
- **Use Case**: Analyze mode persistence
- **Example Query**: `histogram_quantile(0.5, rate(auren_neuros_mode_duration_seconds_bucket[24h]))`

### Cognitive Processing

#### `auren_neuros_hypothesis_generated_total`
- **Type**: Counter
- **Description**: Hypotheses generated by NEUROS
- **Labels**: 
  - `category`: health, performance, recovery, optimization
  - `confidence_level`: low, medium, high
- **Use Case**: Track hypothesis generation
- **Example Query**: `sum by (category) (rate(auren_neuros_hypothesis_generated_total[1h]))`

#### `auren_neuros_pattern_recognition_total`
- **Type**: Counter
- **Description**: Patterns recognized by NEUROS
- **Labels**: 
  - `pattern_type`: sleep, activity, stress, recovery
  - `significance`: low, medium, high
- **Use Case**: Monitor pattern detection
- **Example Query**: `sum by (pattern_type) (increase(auren_neuros_pattern_recognition_total[24h]))`

---

## 📈 Biometric Event Metrics

### Event Processing

#### `auren_biometric_events_processed_total`
- **Type**: Counter
- **Description**: Total biometric events processed
- **Labels**: 
  - `device_type`: oura, whoop, healthkit
  - `event_type`: sleep, activity, readiness
  - `user_id_hash`: Hashed user ID
- **Use Case**: Track event volume by type
- **Example Query**: `sum by (device_type, event_type) (rate(auren_biometric_events_processed_total[5m]))`

#### `auren_biometric_event_values`
- **Type**: Histogram
- **Description**: Distribution of biometric values
- **Labels**: 
  - `device_type`: oura, whoop, healthkit
  - `metric_type`: heart_rate, hrv, temperature, etc.
  - `unit`: bpm, ms, celsius, etc.
- **Buckets**: 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200
- **Use Case**: Monitor biometric value distributions
- **Example Query**: `histogram_quantile(0.5, rate(auren_biometric_event_values_bucket[24h]))`

### Data Quality

#### `auren_biometric_anomalies_detected_total`
- **Type**: Counter
- **Description**: Anomalies in biometric data
- **Labels**: 
  - `device_type`: oura, whoop, healthkit
  - `anomaly_type`: out_of_range, missing_data, inconsistent
  - `severity`: low, medium, high
- **Use Case**: Track data quality issues
- **Example Query**: `sum by (anomaly_type, severity) (increase(auren_biometric_anomalies_detected_total[24h]))`

#### `auren_biometric_data_quality_score`
- **Type**: Gauge
- **Description**: Data quality score (0-1)
- **Labels**: 
  - `device_type`: oura, whoop, healthkit
  - `user_id_hash`: Hashed user ID
- **Use Case**: Monitor data quality by device
- **Example Query**: `avg by (device_type) (auren_biometric_data_quality_score)`

---

## 🚀 Streaming & Kafka Metrics

#### `auren_kafka_messages_sent_total`
- **Type**: Counter
- **Description**: Messages sent to Kafka
- **Labels**: 
  - `topic`: biometric-events, memory-operations, etc.
  - `status`: success, failed
- **Use Case**: Monitor message flow
- **Example Query**: `sum by (topic) (rate(auren_kafka_messages_sent_total[5m]))`

#### `auren_kafka_message_send_duration_seconds`
- **Type**: Histogram
- **Description**: Time to send message to Kafka
- **Labels**: 
  - `topic`: Topic name
- **Buckets**: 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0
- **Use Case**: Monitor Kafka latency
- **Example Query**: `histogram_quantile(0.99, rate(auren_kafka_message_send_duration_seconds_bucket[5m]))`

#### `auren_kafka_batch_size`
- **Type**: Histogram
- **Description**: Size of Kafka batches
- **Labels**: 
  - `topic`: Topic name
- **Buckets**: 1, 5, 10, 50, 100, 500, 1000
- **Use Case**: Monitor batching efficiency
- **Example Query**: `histogram_quantile(0.95, rate(auren_kafka_batch_size_bucket[1h]))`

---

## 💻 System Health Metrics

#### `auren_system`
- **Type**: Info
- **Description**: System information
- **Labels**: 
  - `version`: Application version
  - `environment`: production, staging
  - `deployment`: docker, kubernetes
- **Use Case**: Track deployments
- **Example Query**: `auren_system_info`

#### `auren_database_connections_active`
- **Type**: Gauge
- **Description**: Active database connections
- **Labels**: 
  - `database`: postgres, redis
  - `pool_name`: default, read_replica
- **Use Case**: Monitor connection pools
- **Example Query**: `sum by (database) (auren_database_connections_active)`

#### `auren_api_endpoint_availability`
- **Type**: Gauge
- **Description**: Endpoint availability (0=down, 1=up)
- **Labels**: 
  - `endpoint`: /health, /metrics, /webhooks/*
  - `method`: GET, POST
- **Use Case**: Monitor endpoint health
- **Example Query**: `min by (endpoint) (auren_api_endpoint_availability)`

---

## 📏 Standard Prometheus Metrics

In addition to custom metrics, AUREN exports standard Prometheus metrics:

- `python_gc_*`: Garbage collection metrics
- `python_info`: Python version info
- `process_*`: Process CPU, memory, file descriptors
- `http_*`: HTTP request metrics (if using middleware)

---

## 🏷️ Metric Naming Standards

1. **Prefix**: All custom metrics start with `auren_`
2. **Type Suffix**: 
   - `_total` for counters
   - `_seconds` for durations
   - `_bytes` for sizes
   - `_ratio` or `_rate` for percentages
3. **Units**: Include units in metric names when applicable
4. **Labels**: Use consistent label names across metrics

---

*This catalog is the authoritative source for all AUREN metrics. Update when adding new metrics.* 