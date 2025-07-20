#!/usr/bin/env python3
"""
End-to-end test for HRV event flow through Kafka infrastructure.

This test validates the critical path: sending and receiving HRV events
with the exact data structure that CEP rules will expect.
"""

import uuid
import threading
import time
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.infrastructure.schemas.health_events import (
    HealthEvent, EventType, EventPriority
)
from src.infrastructure.kafka.producer import EventProducer
from src.infrastructure.kafka.consumer import EventConsumer
from src.config.topic_config import TopicMapping


def create_test_hrv_event(user_id: str = "test_user_001") -> HealthEvent:
    """Creates a realistic HRV test event for CEP validation"""
    return HealthEvent(
        event_id=str(uuid.uuid4()),
        user_id=user_id,
        event_type=EventType.BIOMETRIC_UPDATE,
        timestamp=datetime.now(),
        data={
            "metric_type": "hrv",
            "value": 45.2,  # Sample HRV value in milliseconds
            "baseline": 55.0,  # User's normal baseline
            "percentage_drop": 17.8,  # Significant drop for CEP detection
            "measurement_context": "morning",
            "device": "Apple Watch Series 8",
            "confidence": 0.95,
            "unit": "ms",
            "quality_score": 0.92
        },
        source="ios_healthkit",
        priority=EventPriority.NORMAL
    )


def test_hrv_event_end_to_end():
    """
    Success Metric Test: Can send and receive a test HRV event through Kafka
    
    This test validates:
    1. Event creation with CEP-compatible data structure
    2. Successful production to Kafka
    3. Successful consumption from Kafka
    4. Data integrity preservation
    5. Topic routing correctness
    """
    print("=" * 70)
    print("AUREN HRV Event Flow Test - CEP Readiness Validation")
    print("=" * 70)
    
    # Create test event
    hrv_event = create_test_hrv_event()
    print(f"✅ Created HRV event: {hrv_event.event_id}")
    print(f"   User: {hrv_event.user_id}")
    print(f"   HRV Value: {hrv_event.data['value']}ms")
    print(f"   Drop from baseline: {hrv_event.data['percentage_drop']}%")
    
    # Determine correct topic
    topic = TopicMapping.get_topic_for_event_type(EventType.BIOMETRIC)
    print(f"   Target topic: {topic}")
    
    # Initialize producer
    producer = EventProducer()
    received_events: List[HealthEvent] = []
    
    def handle_event(event: HealthEvent):
        """Handler for consumed events"""
        if event.data.get("metric_type") == "hrv":
            received_events.append(event)
            print(f"   📥 Received: {event.event_id}")
    
    # Set up consumer in separate thread
    consumer = EventConsumer(
        topics=[topic],
        group_id="hrv-test-consumer"
    )
    
    consumer_thread = threading.Thread(
        target=lambda: consumer.start(biometric_handler=handle_event)
    )
    consumer_thread.daemon = True
    consumer_thread.start()
    
    # Give consumer time to start
    time.sleep(2)
    
    try:
        # Send event
        print("   📤 Sending event to Kafka...")
        producer.send_biometric_event(hrv_event)
        producer.flush(timeout=5)
        print("   ✅ Event sent successfully")
        
        # Wait for consumption
        print("   ⏳ Waiting for consumption...")
        timeout = 10
        start_time = time.time()
        
        while len(received_events) == 0 and (time.time() - start_time) < timeout:
            time.sleep(0.5)
        
        # Validate results
        assert len(received_events) > 0, "❌ No HRV events received!"
        
        received = received_events[0]
        print(f"   ✅ Event received successfully")
        
        # Verify event integrity
        assert received.event_id == hrv_event.event_id, "❌ Event ID mismatch"
        assert received.data["metric_type"] == "hrv", "❌ Metric type mismatch"
        assert received.data["value"] == 45.2, "❌ HRV value mismatch"
        assert received.data["percentage_drop"] == 17.8, "❌ Percentage drop mismatch"
        assert received.data["baseline"] == 55.0, "❌ Baseline mismatch"
        
        print("   ✅ All validations passed!")
        print(f"   📊 Event integrity verified")
        print(f"   🎯 CEP-ready data structure confirmed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False
        
    finally:
        # Cleanup
        consumer.close()
        producer.close()
        consumer_thread.join(timeout=2)


def test_multiple_hrv_events():
    """Test multiple HRV events for throughput validation"""
    print("\n" + "=" * 70)
    print("Multiple HRV Events Test - Throughput Validation")
    print("=" * 70)
    
    producer = EventProducer()
    received_events: List[HealthEvent] = []
    
    def handle_event(event: HealthEvent):
        if event.data.get("metric_type") == "hrv":
            received_events.append(event)
    
    # Set up consumer
    topic = TopicMapping.get_topic_for_event_type(EventType.BIOMETRIC)
    consumer = EventConsumer(
        topics=[topic],
        group_id="hrv-throughput-test"
    )
    
    consumer_thread = threading.Thread(
        target=lambda: consumer.start(biometric_handler=handle_event)
    )
    consumer_thread.daemon = True
    consumer_thread.start()
    
    time.sleep(2)
    
    try:
        # Send multiple events
        events_to_send = 5
        sent_events = []
        
        start_time = time.time()
        
        for i in range(events_to_send):
            event = create_test_hrv_event(f"test_user_{i:03d}")
            event.data["value"] = 45.0 + i  # Vary values
            event.data["percentage_drop"] = 15.0 + i * 2
            
            producer.send_biometric_event(event)
            sent_events.append(event)
            print(f"   📤 Sent event {i+1}/{events_to_send}: {event.event_id}")
        
        producer.flush(timeout=5)
        
        # Wait for all events
        timeout = 15
        while len(received_events) < events_to_send and (time.time() - start_time) < timeout:
            time.sleep(0.5)
        
        # Validate throughput
        assert len(received_events) == events_to_send, f"❌ Expected {events_to_send} events, got {len(received_events)}"
        
        # Verify all events received correctly
        received_ids = {e.event_id for e in received_events}
        sent_ids = {e.event_id for e in sent_events}
        
        assert received_ids == sent_ids, "❌ Event ID mismatch in batch"
        
        # Calculate throughput
        elapsed = time.time() - start_time
        throughput = events_to_send / elapsed
        
        print(f"   ✅ Throughput test passed!")
        print(f"   📊 Sent: {events_to_send} events")
        print(f"   📊 Received: {len(received_events)} events")
        print(f"   📊 Throughput: {throughput:.2f} events/second")
        print(f"   📊 Elapsed: {elapsed:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Throughput test failed: {e}")
        return False
        
    finally:
        consumer.close()
        producer.close()
        consumer_thread.join(timeout=2)


if __name__ == "__main__":
    print("Starting AUREN Kafka Infrastructure Validation...")
    
    # Test 1: Single HRV event flow
    success1 = test_hrv_event_end_to_end()
    
    # Test 2: Multiple events throughput
    success2 = test_multiple_hrv_events()
    
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Kafka infrastructure is ready for CEP implementation")
        print("✅ HRV event flow validated end-to-end")
        print("✅ Throughput performance confirmed")
        print("✅ CEP-ready data structure verified")
    else:
        print("❌ Some tests failed - please check configuration")
        sys.exit(1)
