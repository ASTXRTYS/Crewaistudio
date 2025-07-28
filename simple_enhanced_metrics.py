#!/usr/bin/env python3
"""
Simple script to add custom metrics to existing complete_biometric_system.py
"""

import re

# Read the current file
with open('complete_biometric_system.py', 'r') as f:
    content = f.read()

# Find the metrics endpoint
metrics_endpoint_pattern = r'(@app\.get\("/metrics"\)\s*async def get_metrics.*?\n)(.*?)(return Response)'

# Create enhanced metrics function
enhanced_metrics = '''    """Expose Prometheus metrics with AUREN custom metrics"""
    # Define custom AUREN metrics
    webhook_counter = Counter('auren_webhooks_total', 'Total webhooks received', ['device_type'])
    memory_operations = Counter('auren_memory_tier_operations_total', 'Memory tier operations', ['tier', 'operation'])
    
    # Increment webhook counter for demonstration
    # In production, this would be incremented in the actual webhook handlers
    webhook_counter.labels(device_type='demo').inc(0)
    
    # Add memory tier metrics for demonstration
    memory_operations.labels(tier='hot', operation='read').inc(0)
    memory_operations.labels(tier='warm', operation='write').inc(0)
    memory_operations.labels(tier='cold', operation='archive').inc(0)
    
    '''

# Replace the metrics function content
def replace_metrics(match):
    return match.group(1) + enhanced_metrics + match.group(3)

# Apply the replacement
content = re.sub(metrics_endpoint_pattern, replace_metrics, content, flags=re.DOTALL)

# Add Counter import if not present
if 'from prometheus_client import' in content and 'Counter' not in content:
    content = content.replace(
        'from prometheus_client import',
        'from prometheus_client import Counter,'
    )

# Write the enhanced file
with open('complete_biometric_system_enhanced_simple.py', 'w') as f:
    f.write(content)

print("✅ Created simple enhanced metrics version")
print("   - Added webhook counter")
print("   - Added memory tier operations counter")
print("   - Minimal changes to avoid syntax errors") 