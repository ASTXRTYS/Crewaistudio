"""
Prometheus Metrics Implementation for AUREN Biometric API
Quick implementation to make metrics visible in Grafana
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Initialize metrics
webhook_events = Counter(
    'auren_webhook_events_total', 
    'Total webhook events received', 
    ['device_type', 'event_type']
)

processing_time = Histogram(
    'auren_processing_duration_seconds', 
    'Time spent processing events',
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

active_webhooks = Gauge(
    'auren_active_webhooks', 
    'Number of webhooks currently being processed'
)

last_webhook_timestamp = Gauge(
    'auren_last_webhook_timestamp',
    'Timestamp of last webhook received',
    ['device_type']
)

# User metrics
active_users = Gauge('auren_active_users', 'Number of active users in the system')
user_readiness = Gauge('auren_user_readiness', 'Latest readiness score by user', ['user_id'])
user_hrv = Gauge('auren_user_hrv', 'Latest HRV score by user', ['user_id'])
user_recovery = Gauge('auren_user_recovery', 'Latest recovery score by user', ['user_id'])

# NEUROS metrics
neuros_mode = Gauge('auren_neuros_mode', 'Current NEUROS mode (1=active, 0=inactive)', ['mode'])
neuros_recommendations = Counter(
    'auren_neuros_recommendations_total',
    'Total recommendations made by NEUROS',
    ['mode', 'recommendation_type']
)

# System health metrics
api_health_status = Gauge('auren_api_health_status', 'API health status (1=healthy, 0=unhealthy)')
database_connections = Gauge('auren_database_connections', 'Number of active database connections')
kafka_lag = Gauge('auren_kafka_consumer_lag', 'Kafka consumer lag in messages')

def record_webhook_metric(device_type: str, event_type: str, user_id: str, data: dict):
    """Record metrics for incoming webhook"""
    # Increment counter
    webhook_events.labels(device_type=device_type, event_type=event_type).inc()
    
    # Update last timestamp
    last_webhook_timestamp.labels(device_type=device_type).set_to_current_time()
    
    # Update user-specific gauges based on data
    if 'readiness_score' in data:
        user_readiness.labels(user_id=user_id).set(data['readiness_score'])
    
    if 'hrv_balance' in data or 'hrv_rmssd' in data:
        hrv_value = data.get('hrv_balance', data.get('hrv_rmssd', 0))
        user_hrv.labels(user_id=user_id).set(hrv_value)
    
    if 'recovery_score' in data:
        user_recovery.labels(user_id=user_id).set(data['recovery_score'])

def update_neuros_mode(mode: str):
    """Update NEUROS mode metric"""
    modes = ['baseline', 'recovery', 'performance', 'adaptation', 'alert']
    for m in modes:
        neuros_mode.labels(mode=m).set(1 if m == mode else 0)

def track_processing_time(func):
    """Decorator to track processing time"""
    def wrapper(*args, **kwargs):
        active_webhooks.inc()
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            processing_time.observe(time.time() - start_time)
            return result
        finally:
            active_webhooks.dec()
    return wrapper

def get_metrics_response():
    """Generate Prometheus metrics response"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Quick implementation to add to existing API:
"""
# Add to imports:
from biometric.metrics_implementation import (
    get_metrics_response, 
    record_webhook_metric, 
    track_processing_time,
    api_health_status
)

# Replace existing /metrics endpoint:
@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics():
    return get_metrics_response()

# Add to webhook handlers:
@app.post("/webhooks/{device_type}")
@track_processing_time
async def webhook_handler(device_type: str, request: Request):
    data = await request.json()
    
    # Record metrics
    record_webhook_metric(
        device_type=device_type,
        event_type=data.get('event_type', 'unknown'),
        user_id=data.get('user_id', 'anonymous'),
        data=data.get('data', {})
    )
    
    # ... rest of handler

# Update health endpoint:
@app.get("/health")
async def health_check():
    # ... existing health check
    api_health_status.set(1 if healthy else 0)
    return response
""" 