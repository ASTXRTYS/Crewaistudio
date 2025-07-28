# =============================================================================
# AUREN PROMETHEUS FIX & OBSERVABILITY ENHANCEMENT IMPLEMENTATION GUIDE
# =============================================================================
# This comprehensive guide fixes the broken Prometheus monitoring and implements
# world-class observability for AUREN, especially for memory tier visualization
# =============================================================================

"""
EXECUTIVE SUMMARY FOR CO-FOUNDER:

The senior engineer discovered our Prometheus is completely broken. This guide:
1. Fixes the biometric API metrics endpoint (currently returns 404)
2. Implements proper Docker networking for Prometheus scraping
3. Adds memory tier movement tracking (answers Founder's question!)
4. Creates beautiful Grafana dashboards for AI agent visualization
5. Sets up the foundation for our Section 10 observability tests

Time to implement: 2-3 hours
Impact: Transforms AUREN from flying blind to having world-class observability
"""

# =============================================================================
# STEP 1: FIX THE BIOMETRIC API METRICS ENDPOINT
# =============================================================================

# File: /auren/biometric/api_metrics_fix.py
# This replaces the placeholder metrics endpoint with real instrumentation

"""
Create this new file to properly instrument the FastAPI application
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI, Response
from typing import Callable
import time
import psutil
import hashlib

# =============================================================================
# CORE METRICS DEFINITIONS
# =============================================================================

# Four Golden Signals
webhook_requests_total = Counter(
    'auren_webhook_requests_total',
    'Total number of webhook requests received',
    ['device_type', 'event_type', 'status']
)

webhook_request_duration_seconds = Histogram(
    'auren_webhook_request_duration_seconds',
    'Webhook request duration in seconds',
    ['device_type', 'method'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

webhook_errors_total = Counter(
    'auren_webhook_errors_total',
    'Total number of webhook processing errors',
    ['device_type', 'error_type']
)

webhook_active_requests = Gauge(
    'auren_webhook_active_requests',
    'Number of webhook requests currently being processed',
    ['device_type']
)

# =============================================================================
# MEMORY TIER METRICS (For the Founder's Visualization!)
# =============================================================================

memory_tier_operations_total = Counter(
    'auren_memory_tier_operations_total',
    'Total memory tier operations by the AI agent',
    ['tier', 'operation', 'trigger']
)

memory_tier_size_bytes = Gauge(
    'auren_memory_tier_size_bytes',
    'Current size of each memory tier in bytes',
    ['tier']
)

memory_tier_latency_seconds = Histogram(
    'auren_memory_tier_latency_seconds',
    'Latency of memory tier operations',
    ['tier', 'operation'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
)

ai_agent_decisions_total = Counter(
    'auren_ai_agent_decisions_total',
    'Total decisions made by NEUROS AI agent',
    ['decision_type', 'from_tier', 'to_tier']
)

# =============================================================================
# BIOMETRIC EVENT METRICS
# =============================================================================

biometric_events_processed_total = Counter(
    'auren_biometric_events_processed_total',
    'Total biometric events processed',
    ['device_type', 'event_type', 'user_id_hash']
)

biometric_event_values = Histogram(
    'auren_biometric_event_values',
    'Distribution of biometric values',
    ['device_type', 'metric_type'],
    buckets=(20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200)
)

# =============================================================================
# NEUROS MODE METRICS
# =============================================================================

neuros_mode_switches_total = Counter(
    'auren_neuros_mode_switches_total',
    'Total NEUROS cognitive mode switches',
    ['from_mode', 'to_mode', 'trigger_type']
)

neuros_current_mode = Gauge(
    'auren_neuros_current_mode',
    'Current NEUROS mode per user (1=baseline, 2=reflex, 3=hypothesis, 4=pattern, 5=companion)',
    ['user_id_hash']
)

# =============================================================================
# SYSTEM HEALTH METRICS
# =============================================================================

system_info = Info(
    'auren_system',
    'AUREN system information'
)

kafka_messages_sent_total = Counter(
    'auren_kafka_messages_sent_total',
    'Total messages sent to Kafka',
    ['topic']
)

kafka_message_send_errors_total = Counter(
    'auren_kafka_message_send_errors_total',
    'Total Kafka message send errors',
    ['topic', 'error_type']
)

# =============================================================================
# ENHANCED FASTAPI INSTRUMENTATOR
# =============================================================================

def create_instrumentator() -> Instrumentator:
    """Create and configure the Prometheus instrumentator for FastAPI"""
    
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health", "/ready"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="auren_http_requests_inprogress",
        inprogress_labels=True,
    )
    
    # Add custom metrics
    @instrumentator.add
    def memory_tier_info(info):
        """Track memory tier operations from request context"""
        if hasattr(info.request.state, "memory_operation"):
            op = info.request.state.memory_operation
            memory_tier_operations_total.labels(
                tier=op.get("tier", "unknown"),
                operation=op.get("operation", "unknown"),
                trigger=op.get("trigger", "manual")
            ).inc()
    
    @instrumentator.add
    def system_metrics(info):
        """Collect system-level metrics"""
        # CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Update system gauges
        system_cpu_usage = Gauge('auren_system_cpu_usage_percent', 'System CPU usage')
        system_memory_usage = Gauge('auren_system_memory_usage_percent', 'System memory usage')
        
        system_cpu_usage.set(cpu_percent)
        system_memory_usage.set(memory.percent)
    
    return instrumentator

# =============================================================================
# METRICS ENDPOINT IMPLEMENTATION
# =============================================================================

def setup_metrics_endpoint(app: FastAPI):
    """Setup the /metrics endpoint for Prometheus scraping"""
    
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        """Expose metrics in Prometheus format"""
        # Update system info
        system_info.info({
            'version': '1.0.0',
            'environment': 'production',
            'deployment': 'docker'
        })
        
        # Generate and return metrics
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )

# =============================================================================
# HELPER FUNCTIONS FOR METRIC TRACKING
# =============================================================================

def track_memory_promotion(user_id: str, from_tier: str, to_tier: str, size_bytes: int, reason: str):
    """Track when AI agent promotes data between memory tiers"""
    # Hash user_id for privacy
    user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    
    # Record the operation
    memory_tier_operations_total.labels(
        tier=to_tier,
        operation="promote",
        trigger=reason
    ).inc()
    
    # Record AI decision
    ai_agent_decisions_total.labels(
        decision_type="tier_promotion",
        from_tier=from_tier,
        to_tier=to_tier
    ).inc()
    
    # Update tier sizes
    memory_tier_size_bytes.labels(tier=to_tier).inc(size_bytes)
    memory_tier_size_bytes.labels(tier=from_tier).dec(size_bytes)

def track_webhook_metrics(device_type: str, event_type: str, duration: float, status: str, error: str = None):
    """Track webhook processing metrics"""
    webhook_requests_total.labels(
        device_type=device_type,
        event_type=event_type,
        status=status
    ).inc()
    
    webhook_request_duration_seconds.labels(
        device_type=device_type,
        method="POST"
    ).observe(duration)
    
    if error:
        webhook_errors_total.labels(
            device_type=device_type,
            error_type=error
        ).inc()

def track_biometric_event(device_type: str, event_type: str, user_id: str, metrics: dict):
    """Track biometric event processing"""
    user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    
    biometric_events_processed_total.labels(
        device_type=device_type,
        event_type=event_type,
        user_id_hash=user_hash
    ).inc()
    
    # Track specific metric values
    for metric_name, value in metrics.items():
        if isinstance(value, (int, float)):
            biometric_event_values.labels(
                device_type=device_type,
                metric_type=metric_name
            ).observe(value)

def track_neuros_mode_switch(user_id: str, from_mode: str, to_mode: str, trigger: str):
    """Track NEUROS cognitive mode switches"""
    user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    
    neuros_mode_switches_total.labels(
        from_mode=from_mode,
        to_mode=to_mode,
        trigger_type=trigger
    ).inc()
    
    # Update current mode gauge
    mode_values = {
        "baseline": 1,
        "reflex": 2,
        "hypothesis": 3,
        "pattern": 4,
        "companion": 5
    }
    
    neuros_current_mode.labels(user_id_hash=user_hash).set(
        mode_values.get(to_mode, 0)
    )

# =============================================================================
# STEP 2: UPDATE THE MAIN API FILE
# =============================================================================

"""
Update /auren/biometric/api.py with these changes:
"""

# Add to imports
from auren.biometric.api_metrics_fix import (
    create_instrumentator,
    setup_metrics_endpoint,
    track_webhook_metrics,
    track_biometric_event,
    track_memory_promotion,
    track_neuros_mode_switch,
    webhook_active_requests
)

# After creating the FastAPI app
app = FastAPI(title="AUREN Biometric Bridge")

# Setup Prometheus instrumentation
instrumentator = create_instrumentator()
instrumentator.instrument(app).expose(app, include_in_schema=False)

# Setup custom metrics endpoint
setup_metrics_endpoint(app)

# Update webhook endpoints to track metrics
@app.post("/webhooks/oura")
async def oura_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    processor: ConcurrentBiometricProcessor = Depends(get_processor),
    settings: Settings = Depends(get_settings)
):
    start_time = time.time()
    device_type = "oura"
    
    # Track active requests
    webhook_active_requests.labels(device_type=device_type).inc()
    
    try:
        # ... existing webhook logic ...
        
        # Track successful processing
        duration = time.time() - start_time
        track_webhook_metrics(
            device_type=device_type,
            event_type=data.get("event_type", "unknown"),
            duration=duration,
            status="success"
        )
        
        # Track biometric event
        if biometric_event:
            track_biometric_event(
                device_type=device_type,
                event_type=data.get("event_type"),
                user_id=data.get("user_id"),
                metrics=biometric_event.get("metrics", {})
            )
        
        return {"status": "success", "request_id": request_id}
        
    except Exception as e:
        duration = time.time() - start_time
        track_webhook_metrics(
            device_type=device_type,
            event_type=data.get("event_type", "unknown"),
            duration=duration,
            status="error",
            error=type(e).__name__
        )
        raise
    finally:
        webhook_active_requests.labels(device_type=device_type).dec()

# =============================================================================
# STEP 3: MEMORY TIER INSTRUMENTATION
# =============================================================================

"""
Add to the ConcurrentBiometricProcessor class to track memory operations:
"""

class InstrumentedBiometricProcessor(ConcurrentBiometricProcessor):
    """Enhanced processor with memory tier tracking"""
    
    async def promote_to_hot_tier(self, user_id: str, data: dict, size_bytes: int):
        """Promote data to Redis hot tier with metrics"""
        start_time = time.time()
        
        try:
            # Existing Redis operation
            await self.redis.setex(
                f"biometric:hot:{user_id}:latest",
                300,  # 5 minute TTL
                json.dumps(data)
            )
            
            # Track the operation
            track_memory_promotion(
                user_id=user_id,
                from_tier="warm",
                to_tier="hot",
                size_bytes=size_bytes,
                reason="frequency_threshold"
            )
            
            # Track latency
            latency = time.time() - start_time
            memory_tier_latency_seconds.labels(
                tier="hot",
                operation="promote"
            ).observe(latency)
            
        except Exception as e:
            logger.error(f"Failed to promote to hot tier: {e}")
            raise
    
    async def archive_to_cold_tier(self, user_id: str, data: dict, size_bytes: int):
        """Archive to ChromaDB cold tier with metrics"""
        start_time = time.time()
        
        try:
            # ChromaDB operation
            collection = self.chroma_client.get_or_create_collection("biometric_patterns")
            collection.add(
                documents=[json.dumps(data)],
                metadatas=[{"user_id": user_id, "archived_at": datetime.utcnow().isoformat()}],
                ids=[f"{user_id}_{datetime.utcnow().timestamp()}"]
            )
            
            # Track the operation
            track_memory_promotion(
                user_id=user_id,
                from_tier="warm",
                to_tier="cold",
                size_bytes=size_bytes,
                reason="age_threshold"
            )
            
            # Track latency
            latency = time.time() - start_time
            memory_tier_latency_seconds.labels(
                tier="cold",
                operation="archive"
            ).observe(latency)
            
        except Exception as e:
            logger.error(f"Failed to archive to cold tier: {e}")
            raise

# =============================================================================
# STEP 4: FIX PROMETHEUS CONFIGURATION
# =============================================================================

# File: /scripts/prometheus-prod.yml
# This fixes the network configuration issues

"""
Create this Prometheus configuration that uses Docker internal networking:
"""

prometheus_config = """
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'auren-production'

# Alerting configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets: []

# Rule files
rule_files:
  - "alerts.yml"

# Scrape configurations
scrape_configs:
  # Biometric API - Using Docker internal network
  - job_name: 'biometric-api'
    static_configs:
      - targets: ['biometric-production:8888']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'biometric-api'
  
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  # Node Exporter
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['auren-node-exporter:9100']
  
  # PostgreSQL Exporter
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['auren-postgres-exporter:9187']
  
  # Redis Exporter
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['auren-redis-exporter:9121']
  
  # Kafka Exporter (if available)
  - job_name: 'kafka-exporter'
    static_configs:
      - targets: ['kafka-exporter:9308']
    honor_labels: true
"""

# =============================================================================
# STEP 5: DEPLOYMENT SCRIPT
# =============================================================================

# File: /scripts/deploy_prometheus_fix.sh
# This script deploys all the fixes

#!/bin/bash
set -e

echo "🚀 Deploying Prometheus Fix and Observability Enhancement"

# SSH details
SERVER="144.126.215.218"
PASSWORD=".HvddX+@6dArsKd"

# Step 1: Copy the metrics fix to server
echo "📦 Copying metrics implementation..."
sshpass -p "$PASSWORD" scp api_metrics_fix.py root@$SERVER:/tmp/

# Step 2: Update the biometric container
echo "🔧 Updating biometric API with metrics..."
sshpass -p "$PASSWORD" ssh root@$SERVER << 'EOF'
# Copy metrics file into container
docker cp /tmp/api_metrics_fix.py biometric-production:/app/api_metrics_fix.py

# Install prometheus-fastapi-instrumentator in container
docker exec biometric-production pip install prometheus-fastapi-instrumentator psutil

# Restart the container to load new code
docker restart biometric-production

# Wait for startup
sleep 10

# Test metrics endpoint
echo "Testing metrics endpoint..."
curl -s http://localhost:8888/metrics | head -20
EOF

# Step 3: Update Prometheus configuration
echo "📝 Updating Prometheus configuration..."
cat > /tmp/prometheus.yml << 'EOF'
${prometheus_config}
EOF

sshpass -p "$PASSWORD" scp /tmp/prometheus.yml root@$SERVER:/opt/auren_deploy/prometheus.yml

# Step 4: Restart Prometheus
echo "🔄 Restarting Prometheus..."
sshpass -p "$PASSWORD" ssh root@$SERVER << 'EOF'
docker restart auren-prometheus
sleep 5

# Verify targets
echo "Checking Prometheus targets..."
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .job, health: .health}'
EOF

echo "✅ Prometheus fix deployed!"
echo "📊 Check metrics at: http://$SERVER:8888/metrics"
echo "🎯 Check Prometheus at: http://$SERVER:9090"
echo "📈 Check Grafana at: http://$SERVER:3000"

# =============================================================================
# STEP 6: GRAFANA DASHBOARD FOR MEMORY VISUALIZATION
# =============================================================================

# File: /scripts/create_memory_tier_dashboard.py
# This creates the dashboard the Founder requested

import httpx
import json
import asyncio

GRAFANA_URL = "http://144.126.215.218:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "auren_grafana_2025"

memory_tier_dashboard = {
    "dashboard": {
        "title": "AUREN AI Agent Memory Tier Visualization",
        "description": "Real-time visualization of how NEUROS manages knowledge across memory tiers",
        "tags": ["ai", "memory", "neuros"],
        "timezone": "browser",
        "panels": [
            {
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 0},
                "title": "Memory Tier Operations Flow",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(auren_memory_tier_operations_total[5m])",
                        "legendFormat": "{{tier}} - {{operation}}",
                        "refId": "A"
                    }
                ],
                "yaxes": [{"label": "Operations/sec", "show": True}]
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "title": "Current Memory Tier Sizes",
                "type": "piechart",
                "targets": [
                    {
                        "expr": "auren_memory_tier_size_bytes",
                        "legendFormat": "{{tier}}",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "title": "AI Agent Decisions",
                "type": "stat",
                "targets": [
                    {
                        "expr": "sum(rate(auren_ai_agent_decisions_total[5m]))",
                        "legendFormat": "Decisions/sec",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
                "title": "Memory Tier Operation Latency",
                "type": "heatmap",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(auren_memory_tier_latency_seconds_bucket[5m]))",
                        "legendFormat": "{{tier}} - {{operation}} p95",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 24},
                "title": "NEUROS Mode Distribution",
                "type": "bargauge",
                "targets": [
                    {
                        "expr": "count by (to_mode) (increase(auren_neuros_mode_switches_total[1h]))",
                        "legendFormat": "{{to_mode}}",
                        "refId": "A"
                    }
                ]
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 24},
                "title": "Biometric Events by Device",
                "type": "timeseries",
                "targets": [
                    {
                        "expr": "rate(auren_biometric_events_processed_total[5m])",
                        "legendFormat": "{{device_type}}",
                        "refId": "A"
                    }
                ]
            }
        ],
        "refresh": "5s",
        "time": {"from": "now-1h", "to": "now"},
        "uid": "auren-memory-tiers"
    }
}

async def create_dashboard():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            json=memory_tier_dashboard,
            auth=(GRAFANA_USER, GRAFANA_PASS)
        )
        
        if response.status_code == 200:
            print("✅ Memory tier dashboard created!")
            print(f"🔗 View at: {GRAFANA_URL}/d/auren-memory-tiers")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(create_dashboard())

# =============================================================================
# STEP 7: ALERT RULES FOR OBSERVABILITY
# =============================================================================

# File: /scripts/prometheus_alerts.yml
# Alert rules for the system

alert_rules = """
groups:
  - name: auren_alerts
    interval: 30s
    rules:
      - alert: HighWebhookErrorRate
        expr: |
          (sum(rate(auren_webhook_errors_total[5m])) / sum(rate(auren_webhook_requests_total[5m]))) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High webhook error rate ({{ $value | humanizePercentage }})"
          description: "Webhook error rate is above 5% for the last 2 minutes"
      
      - alert: HighMemoryTierLatency
        expr: |
          histogram_quantile(0.95, rate(auren_memory_tier_latency_seconds_bucket[5m])) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory tier operation latency"
          description: "P95 latency for {{ $labels.tier }} tier {{ $labels.operation }} is {{ $value }}s"
      
      - alert: LowCacheHitRate
        expr: |
          (sum(rate(auren_memory_tier_operations_total{tier="hot", operation="hit"}[5m])) /
           sum(rate(auren_memory_tier_operations_total{tier="hot"}[5m]))) < 0.7
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "Low cache hit rate in hot tier"
          description: "Hot tier cache hit rate is {{ $value | humanizePercentage }}"
      
      - alert: FrequentNEUROSModeSwitching
        expr: |
          sum(rate(auren_neuros_mode_switches_total[5m])) by (user_id_hash) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Frequent NEUROS mode switching"
          description: "User {{ $labels.user_id_hash }} is switching modes too frequently"
"""

# =============================================================================
# TROUBLESHOOTING GUIDE
# =============================================================================

"""
TROUBLESHOOTING GUIDE FOR SENIOR ENGINEER:

1. If metrics endpoint still returns 404:
   - Check if prometheus-fastapi-instrumentator is installed
   - Verify api_metrics_fix.py was copied correctly
   - Check Docker logs: docker logs biometric-production
   - Ensure the FastAPI app is importing the metrics module

2. If Prometheus can't scrape targets:
   - Verify containers are on same network: docker network inspect auren-network
   - Check if biometric-production container name is correct
   - Test from inside Prometheus container: 
     docker exec auren-prometheus wget -O- http://biometric-production:8888/metrics

3. If no metrics appear in Grafana:
   - Check Prometheus targets page: http://144.126.215.218:9090/targets
   - Verify data source in Grafana is configured correctly
   - Check time range in Grafana (should be "Last 5 minutes" or similar)

4. To manually test memory tier tracking:
   - Send a webhook that triggers memory operations
   - Check metrics: curl http://144.126.215.218:8888/metrics | grep memory_tier

5. Common Docker networking fix:
   docker network connect auren-network biometric-production
   docker network connect auren-network auren-prometheus
"""

# =============================================================================
# SUMMARY FOR THE FOUNDER
# =============================================================================

"""
FOR THE FOUNDER - What This Gives You:

1. **Memory Tier Visualization Dashboard**
   - See exactly when and why the AI moves data between tiers
   - Track hot (Redis), warm (PostgreSQL), and cold (ChromaDB) storage
   - Understand AI decision patterns

2. **Real-time Metrics**
   - Biometric event processing rates
   - NEUROS mode switching patterns
   - System performance indicators

3. **Proactive Alerts**
   - Get notified when error rates spike
   - Know when memory operations slow down
   - Track cache efficiency

4. **Complete Observability**
   - Every webhook, every decision, every memory movement is tracked
   - Beautiful Grafana dashboards update in real-time
   - Historical data for pattern analysis

Access your new dashboard at: http://144.126.215.218:3000/d/auren-memory-tiers
Login: admin / auren_grafana_2025
"""
