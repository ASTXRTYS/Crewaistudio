#!/usr/bin/env python3
"""
Script to update the biometric API with Prometheus metrics
"""

import re

# Read the current API file
with open('/app/api.py', 'r') as f:
    content = f.read()

# Add imports at the top after existing imports
import_section = """
# Prometheus metrics imports
from api_metrics_fix import (
    create_instrumentator,
    setup_metrics_endpoint,
    track_webhook_metrics,
    track_biometric_event,
    track_memory_promotion,
    track_neuros_mode_switch,
    track_kafka_message,
    webhook_active_requests,
    InstrumentedBiometricProcessor
)
"""

# Find the imports section and add our imports
import_pattern = r'(from contextlib import asynccontextmanager\n)'
content = re.sub(import_pattern, r'\1\n' + import_section + '\n', content)

# Add instrumentation after app creation
app_pattern = r'(app = FastAPI\(.*?\))'
instrumentation_code = """

# Setup Prometheus instrumentation
instrumentator = create_instrumentator()
instrumentator.instrument(app).expose(app, include_in_schema=False)

# Setup custom metrics endpoint
setup_metrics_endpoint(app)"""

content = re.sub(app_pattern, r'\1' + instrumentation_code, content, flags=re.DOTALL)

# Replace the metrics endpoint
metrics_pattern = r'@app\.get\("/metrics"\).*?(?=@app|\Z)'
content = re.sub(metrics_pattern, '', content, flags=re.DOTALL)

# Update webhook endpoints to track metrics
# Update Oura webhook
oura_pattern = r'(@app\.post\("/webhooks/oura"\)\nasync def oura_webhook\([\s\S]*?\):\n)([\s\S]*?)(return \{"status": "accepted")'
oura_replacement = r'''\1\2    start_time = time.time()
    device_type = "oura"
    
    # Track active requests
    webhook_active_requests.labels(device_type=device_type).inc()
    
    try:
        # Get event data
        data = await request.json()
        
        # Track successful processing
        duration = time.time() - start_time
        track_webhook_metrics(
            device_type=device_type,
            event_type=data.get("event_type", "unknown"),
            duration=duration,
            status="success"
        )
        
        # Track biometric event if available
        if data:
            track_biometric_event(
                device_type=device_type,
                event_type=data.get("event_type", "unknown"),
                user_id=data.get("user_id", "unknown"),
                metrics=data.get("data", {})
            )
        
    except Exception as e:
        duration = time.time() - start_time
        track_webhook_metrics(
            device_type=device_type,
            event_type="unknown",
            duration=duration,
            status="error",
            error=type(e).__name__
        )
        webhook_active_requests.labels(device_type=device_type).dec()
        raise
    finally:
        webhook_active_requests.labels(device_type=device_type).dec()
    
    \3'''

content = re.sub(oura_pattern, oura_replacement, content)

# Similar updates for WHOOP webhook
whoop_pattern = r'(@app\.post\("/webhooks/whoop"\)\nasync def whoop_webhook\([\s\S]*?\):\n)([\s\S]*?)(return \{"status": "accepted")'
whoop_replacement = r'''\1\2    start_time = time.time()
    device_type = "whoop"
    
    # Track active requests
    webhook_active_requests.labels(device_type=device_type).inc()
    
    try:
        # Get event data
        data = await request.json()
        
        # Track successful processing
        duration = time.time() - start_time
        track_webhook_metrics(
            device_type=device_type,
            event_type=data.get("event_type", "unknown"),
            duration=duration,
            status="success"
        )
        
        # Track biometric event if available
        if data:
            track_biometric_event(
                device_type=device_type,
                event_type=data.get("event_type", "unknown"),
                user_id=data.get("user_id", "unknown"),
                metrics=data.get("data", {})
            )
        
    except Exception as e:
        duration = time.time() - start_time
        track_webhook_metrics(
            device_type=device_type,
            event_type="unknown",
            duration=duration,
            status="error",
            error=type(e).__name__
        )
        webhook_active_requests.labels(device_type=device_type).dec()
        raise
    finally:
        webhook_active_requests.labels(device_type=device_type).dec()
    
    \3'''

content = re.sub(whoop_pattern, whoop_replacement, content)

# Update HealthKit webhook similarly
healthkit_pattern = r'(@app\.post\("/webhooks/healthkit"\)\nasync def healthkit_webhook\([\s\S]*?\):\n)([\s\S]*?)(return \{"status": "accepted")'
healthkit_replacement = r'''\1\2    start_time = time.time()
    device_type = "healthkit"
    
    # Track active requests
    webhook_active_requests.labels(device_type=device_type).inc()
    
    try:
        # Get event data
        data = await request.json()
        
        # Track successful processing
        duration = time.time() - start_time
        track_webhook_metrics(
            device_type=device_type,
            event_type="batch_update",
            duration=duration,
            status="success"
        )
        
        # Track biometric event if available
        if data:
            track_biometric_event(
                device_type=device_type,
                event_type="batch_update",
                user_id=data.get("user_id", "unknown"),
                metrics=data.get("data", {})
            )
        
    except Exception as e:
        duration = time.time() - start_time
        track_webhook_metrics(
            device_type=device_type,
            event_type="batch_update",
            duration=duration,
            status="error",
            error=type(e).__name__
        )
        webhook_active_requests.labels(device_type=device_type).dec()
        raise
    finally:
        webhook_active_requests.labels(device_type=device_type).dec()
    
    \3'''

content = re.sub(healthkit_pattern, healthkit_replacement, content)

# Write the updated content
with open('/app/api.py', 'w') as f:
    f.write(content)

print("✅ API updated with Prometheus metrics!")
print("✅ Metrics endpoint: /metrics")
print("✅ Webhook tracking enabled")
print("✅ Memory tier instrumentation ready") 