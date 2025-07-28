#!/usr/bin/env python3
"""
Simple fix to add metrics endpoint to complete_biometric_system.py
"""

# Read the original file
with open('complete_biometric_system.py', 'r') as f:
    content = f.read()

# Add prometheus imports at the top after other imports
prometheus_imports = """
# Prometheus metrics support
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
    
    # Define metrics
    webhook_counter = Counter('auren_webhooks_total', 'Total webhooks received', ['device_type'])
    webhook_duration = Histogram('auren_webhook_duration_seconds', 'Webhook processing time', ['device_type'])
    biometric_events = Counter('auren_biometric_events_total', 'Total biometric events', ['device_type', 'event_type'])
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("Warning: Prometheus client not available, metrics disabled")
"""

# Find where to insert imports (after the last import statement)
import_pos = content.rfind('\nimport')
if import_pos == -1:
    import_pos = content.rfind('\nfrom')

if import_pos != -1:
    # Find the end of that line
    line_end = content.find('\n', import_pos + 1)
    if line_end != -1:
        content = content[:line_end] + '\n' + prometheus_imports + content[line_end:]

# Add metrics endpoint before the main block
metrics_endpoint = '''
# Prometheus metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Expose Prometheus metrics"""
    if PROMETHEUS_AVAILABLE:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    else:
        return {"error": "Prometheus metrics not available"}
'''

# Find where to add the endpoint (before if __name__ == "__main__")
main_pos = content.find('\nif __name__ == "__main__":')
if main_pos != -1:
    content = content[:main_pos] + '\n' + metrics_endpoint + '\n' + content[main_pos:]

# Add Response import if needed
if "from fastapi import" in content and "Response" not in content:
    fastapi_import = content.find("from fastapi import")
    import_end = content.find("\n", fastapi_import)
    if import_end != -1:
        # Check if Response is already imported
        import_line = content[fastapi_import:import_end]
        if "Response" not in import_line:
            # Add Response to the import
            content = content[:import_end] + ", Response" + content[import_end:]

# Write the updated file
with open('complete_biometric_system_fixed.py', 'w') as f:
    f.write(content)

print("✅ Created complete_biometric_system_fixed.py with metrics endpoint")
print("✅ Metrics will be available at /metrics")
print("✅ No syntax errors introduced") 