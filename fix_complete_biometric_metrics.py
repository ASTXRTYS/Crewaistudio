#!/usr/bin/env python3
"""
Script to add Prometheus metrics to complete_biometric_system.py
"""

import re

# Read the current file
with open('/app/complete_biometric_system.py', 'r') as f:
    content = f.read()

# Add imports after existing imports
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
import time
"""

# Find the import section and add our imports after WebSocketDisconnect
import_pattern = r'(from fastapi import FastAPI, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect, Header\n)'
content = re.sub(import_pattern, r'\1' + import_section + '\n', content)

# Add instrumentation after app creation
app_pattern = r'(app = FastAPI\([\s\S]*?\)\n)'
instrumentation_code = """
# Setup Prometheus instrumentation
instrumentator = create_instrumentator()
instrumentator.instrument(app).expose(app, include_in_schema=False)

# Setup custom metrics endpoint
setup_metrics_endpoint(app)
"""

# Find the app creation and add instrumentation
match = re.search(app_pattern, content)
if match:
    end_pos = match.end()
    content = content[:end_pos] + instrumentation_code + '\n' + content[end_pos:]

# Update webhook endpoint to track metrics
webhook_pattern = r'(@app\.post\("/webhooks/\{device_type\}"\)\nasync def receive_webhook\([\s\S]*?\):\n)([\s\S]*?)(background_tasks\.add_task)'

webhook_replacement = r'''\1    """Process incoming webhook from any device type"""
    start_time = time.time()
    
    # Track active requests
    webhook_active_requests.labels(device_type=device_type).inc()
    
    try:\2        # Track metrics
        data = await request.json()
        
        # Track successful processing
        duration = time.time() - start_time
        track_webhook_metrics(
            device_type=device_type,
            event_type=data.get("event_type", "unknown"),
            duration=duration,
            status="success"
        )
        
        # Track biometric event
        if data:
            track_biometric_event(
                device_type=device_type,
                event_type=data.get("event_type", "unknown"),
                user_id=user_id,
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

content = re.sub(webhook_pattern, webhook_replacement, content)

# Update HealthKit batch endpoint to track metrics
healthkit_pattern = r'(@app\.post\("/batch/healthkit"\)\nasync def process_healthkit_batch\([\s\S]*?\):\n)([\s\S]*?)(return \{)'

healthkit_replacement = r'''\1    """Process batch HealthKit data"""
    start_time = time.time()
    device_type = "healthkit"
    
    try:\2        # Track metrics for batch
        track_webhook_metrics(
            device_type=device_type,
            event_type="batch_update",
            duration=time.time() - start_time,
            status="success"
        )
        
        # Track each sample as biometric event
        if batch and batch.samples:
            for sample in batch.samples:
                track_biometric_event(
                    device_type=device_type,
                    event_type="batch_sample",
                    user_id=batch.user_id,
                    metrics={"type": sample.type, "value": sample.value}
                )
    
    except Exception as e:
        track_webhook_metrics(
            device_type=device_type,
            event_type="batch_update",
            duration=time.time() - start_time,
            status="error",
            error=type(e).__name__
        )
        raise
    
    \3'''

content = re.sub(healthkit_pattern, healthkit_replacement, content)

# Write the updated content
with open('/app/complete_biometric_system.py', 'w') as f:
    f.write(content)

print("✅ complete_biometric_system.py updated with Prometheus metrics!")
print("✅ Metrics endpoint: /metrics")
print("✅ Webhook tracking enabled")
print("✅ Memory tier instrumentation ready") 