#!/usr/bin/env python3
"""
Fix the complete_biometric_system.py file more carefully
"""

# First, let's restore the original from backup and apply a simpler fix
import shutil
import re

# Backup current broken file
shutil.copy('/app/complete_biometric_system.py', '/app/complete_biometric_system.broken.py')

# Try to restore from a possible original
try:
    shutil.copy('/app/complete_biometric_system.py.orig', '/app/complete_biometric_system.py')
except:
    print("No backup found, will fix current file")

# Read the file
with open('/app/complete_biometric_system.py', 'r') as f:
    content = f.read()

# First, let's just add the imports without breaking anything
import_addition = """
# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
    from prometheus_fastapi_instrumentator import Instrumentator
    
    # Initialize metrics
    webhook_requests_total = Counter(
        'auren_webhook_requests_total',
        'Total webhook requests',
        ['device_type', 'event_type', 'status']
    )
    
    webhook_duration = Histogram(
        'auren_webhook_duration_seconds', 
        'Webhook processing duration',
        ['device_type']
    )
    
    METRICS_ENABLED = True
except ImportError:
    print("Prometheus metrics not available")
    METRICS_ENABLED = False
"""

# Add imports after the existing imports
if "from typing import" in content:
    content = content.replace(
        "from typing import",
        import_addition + "\nfrom typing import"
    )

# Now add a simple metrics endpoint after all other endpoints
metrics_endpoint = '''

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    if METRICS_ENABLED:
        from fastapi.responses import Response
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    else:
        return {"error": "Metrics not enabled"}
'''

# Find the last endpoint and add metrics after it
if "@app.websocket" in content:
    # Find the last occurrence
    last_websocket = content.rfind("@app.websocket")
    # Find the end of that function (look for the next function or end of file)
    next_function = content.find("\n@", last_websocket + 1)
    if next_function == -1:
        # No more functions, add at end
        content = content + metrics_endpoint
    else:
        # Add before the next function
        content = content[:next_function] + metrics_endpoint + content[next_function:]
else:
    # Just add at the end
    content = content + metrics_endpoint

# Add simple metric tracking to webhook endpoint without breaking try/except
webhook_tracking = '''
    # Track metrics if available
    if METRICS_ENABLED:
        import time
        start_time = time.time()
        webhook_requests_total.labels(
            device_type=device_type,
            event_type="webhook",
            status="received"
        ).inc()
'''

# Find webhook endpoint and add tracking at the beginning of the function
webhook_match = re.search(r'(@app\.post\("/webhooks/\{device_type\}"\)\nasync def receive_webhook[^:]+:\n)', content)
if webhook_match:
    func_start = webhook_match.end()
    # Find the docstring end
    docstring_end = content.find('"""', func_start)
    if docstring_end != -1:
        docstring_end = content.find('"""', docstring_end + 3) + 3
        content = content[:docstring_end] + '\n' + webhook_tracking + content[docstring_end:]

# Write the fixed content
with open('/app/complete_biometric_system.py', 'w') as f:
    f.write(content)

print("✅ Fixed complete_biometric_system.py with simple metrics")
print("✅ Added /metrics endpoint")
print("✅ Added basic webhook tracking") 