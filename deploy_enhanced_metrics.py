#!/usr/bin/env python3
"""
Deploy enhanced metrics to the AUREN biometric API
"""

import re

# Read the current API file
with open('complete_biometric_system.py', 'r') as f:
    content = f.read()

# Add enhanced metrics imports after prometheus imports
enhanced_imports = """
# Enhanced AUREN metrics
from enhanced_api_metrics import (
    metrics_tracker,
    WebhookMetrics,
    MemoryOperationMetrics,
    system_info
)
"""

# Find where to insert enhanced imports
prometheus_import_pos = content.find("from prometheus_client import")
if prometheus_import_pos != -1:
    # Find the end of that line
    line_end = content.find('\n', prometheus_import_pos)
    if line_end != -1:
        # Find the next import or empty line
        next_line_start = line_end + 1
        while next_line_start < len(content) and content[next_line_start:next_line_start+6] in ['from ', 'import']:
            next_line_start = content.find('\n', next_line_start) + 1
        
        content = content[:next_line_start] + enhanced_imports + '\n' + content[next_line_start:]

# Update webhook endpoints to use enhanced metrics
# Find Oura webhook
oura_pattern = r'(@app\.post\("/webhooks/oura"\)\nasync def oura_webhook\([^:]+:\n)(.*?)(\n    return)'
oura_replacement = r'''\1    """Process Oura webhook with enhanced metrics"""
    async with WebhookMetrics("oura") as metrics:
        # Get request data
        data = await request.json()
        metrics.event_type = data.get("event_type", "unknown")
        metrics.payload_size = len(await request.body())
        
        # Get user ID from webhook
        user_id = data.get("user_id", "unknown")
        
        # Track biometric event
        if data.get("data"):
            metrics_tracker.track_biometric_event(
                device_type="oura",
                event_type=data.get("event_type", "unknown"),
                user_id=user_id,
                metrics=data.get("data", {}),
                quality_score=0.95  # Oura has high quality data
            )
        
        # Process webhook (existing logic)
        processor = get_processor()
        await processor.process_biometric_event(BiometricEvent(
            device_type=WearableType.OURA,
            event_type=data.get("event_type"),
            user_id=user_id,
            data=data.get("data", {}),
            timestamp=datetime.utcnow()
        ))
        
        # Log the event
        logger.info(f"Processed Oura webhook for user {user_id}"){REPLACEMENT_MARKER}\3'''

# Mark where we need to preserve existing content
oura_replacement = oura_replacement.replace('{REPLACEMENT_MARKER}', r'\2')
content = re.sub(oura_pattern, oura_replacement, content, flags=re.DOTALL)

# Similar for WHOOP webhook
whoop_pattern = r'(@app\.post\("/webhooks/whoop"\)\nasync def whoop_webhook\([^:]+:\n)(.*?)(\n    return)'
whoop_replacement = r'''\1    """Process WHOOP webhook with enhanced metrics"""
    async with WebhookMetrics("whoop") as metrics:
        # Get request data
        data = await request.json()
        metrics.event_type = data.get("event_type", "unknown")
        metrics.payload_size = len(await request.body())
        
        # Get user ID
        user_id = data.get("user_id", "unknown")
        
        # Track biometric event
        if data.get("data"):
            metrics_tracker.track_biometric_event(
                device_type="whoop",
                event_type=data.get("event_type", "unknown"),
                user_id=user_id,
                metrics=data.get("data", {}),
                quality_score=0.9  # WHOOP has good quality data
            )
        
        # Process webhook (existing logic)
        processor = get_processor()
        await processor.process_biometric_event(BiometricEvent(
            device_type=WearableType.WHOOP,
            event_type=data.get("event_type"),
            user_id=user_id,
            data=data.get("data", {}),
            timestamp=datetime.utcnow()
        ))
        
        logger.info(f"Processed WHOOP webhook for user {user_id}"){REPLACEMENT_MARKER}\3'''

whoop_replacement = whoop_replacement.replace('{REPLACEMENT_MARKER}', r'\2')
content = re.sub(whoop_pattern, whoop_replacement, content, flags=re.DOTALL)

# Update HealthKit batch endpoint
healthkit_pattern = r'(@app\.post\("/batch/healthkit"\)\nasync def process_healthkit_batch\([^:]+:\n)(.*?)(\n    return)'
healthkit_replacement = r'''\1    """Process HealthKit batch with enhanced metrics"""
    async with WebhookMetrics("healthkit", "batch_update") as metrics:
        # Calculate payload size
        body = await request.body()
        metrics.payload_size = len(body)
        
        # Parse batch data
        batch = HealthKitBatch.parse_raw(body)
        
        # Track each sample
        for sample in batch.samples:
            metrics_tracker.track_biometric_event(
                device_type="healthkit",
                event_type="batch_sample",
                user_id=batch.user_id,
                metrics={"type": sample.type, "value": sample.value},
                quality_score=0.85  # HealthKit quality varies
            )
        
        # Process batch (existing logic)
        processor = get_processor()
        await processor.process_healthkit_batch(batch)
        
        logger.info(f"Processed {len(batch.samples)} HealthKit samples"){REPLACEMENT_MARKER}\3'''

healthkit_replacement = healthkit_replacement.replace('{REPLACEMENT_MARKER}', r'\2')
content = re.sub(healthkit_pattern, healthkit_replacement, content, flags=re.DOTALL)

# Add memory tier tracking to ConcurrentBiometricProcessor
# First, find the class definition
processor_class_pattern = r'(class ConcurrentBiometricProcessor:)'
processor_enhancement = r'''\1
    """Enhanced biometric processor with memory tier tracking"""
    
    async def promote_to_hot_tier(self, user_id: str, data: dict):
        """Promote data to Redis hot tier with metrics"""
        async with MemoryOperationMetrics("hot", "promote", "frequency_threshold") as metrics:
            data_str = json.dumps(data)
            metrics.size_bytes = len(data_str.encode('utf-8'))
            
            # Store in Redis
            await self.redis.setex(
                f"biometric:hot:{user_id}:latest",
                300,  # 5 minute TTL
                data_str
            )
            
            # Track the promotion
            metrics_tracker.track_memory_promotion(
                user_id=user_id,
                from_tier="warm",
                to_tier="hot",
                size_bytes=metrics.size_bytes,
                reason="frequency_threshold",
                duration=0.0  # Will be calculated by context manager
            )
    
    async def archive_to_cold_tier(self, user_id: str, data: dict):
        """Archive to ChromaDB cold tier with metrics"""
        async with MemoryOperationMetrics("cold", "archive", "age_threshold") as metrics:
            data_str = json.dumps(data)
            metrics.size_bytes = len(data_str.encode('utf-8'))
            
            if hasattr(self, 'chroma_client') and self.chroma_client:
                # Store in ChromaDB
                collection = self.chroma_client.get_or_create_collection("biometric_patterns")
                collection.add(
                    documents=[data_str],
                    metadatas=[{"user_id": user_id, "archived_at": datetime.utcnow().isoformat()}],
                    ids=[f"{user_id}_{datetime.utcnow().timestamp()}"]
                )
                
                # Track the archival
                metrics_tracker.track_memory_promotion(
                    user_id=user_id,
                    from_tier="warm",
                    to_tier="cold",
                    size_bytes=metrics.size_bytes,
                    reason="age_threshold",
                    duration=0.0
                )'''

# Check if the enhancements already exist
if "promote_to_hot_tier" not in content:
    content = re.sub(processor_class_pattern, processor_enhancement, content)

# Add system info update in lifespan
lifespan_pattern = r'(async def lifespan\(app: FastAPI\):.*?)(logger\.info\("Biometric Bridge API starting")'
lifespan_enhancement = r'''\1    # Update system info for metrics
    system_info.info({
        'version': '1.0.0',
        'environment': 'production',
        'deployment': 'docker',
        'enhanced_metrics': 'true'
    })
    
    \2'''

content = re.sub(lifespan_pattern, lifespan_enhancement, content, flags=re.DOTALL)

# Write the enhanced file
with open('complete_biometric_system_enhanced.py', 'w') as f:
    f.write(content)

print("✅ Created complete_biometric_system_enhanced.py with:")
print("  - Enhanced webhook metrics tracking")
print("  - Memory tier operation metrics")
print("  - Biometric event tracking")
print("  - System info updates")
print("\n📊 Next: Deploy and create enhanced Grafana dashboards") 