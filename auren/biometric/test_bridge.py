#!/usr/bin/env python3
"""
Test script for AUREN Biometric Bridge
Simulates biometric events to test mode switching
"""

import asyncio
import json
from datetime import datetime
from aiokafka import AIOKafkaProducer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BIOMETRIC.TEST")

# Test biometric events
TEST_EVENTS = [
    {
        "device_type": "oura_ring",
        "user_id": "test_user_001",
        "timestamp": datetime.now().isoformat(),
        "readings": [
            {
                "metric": "hrv",
                "value": 65.0,  # Normal HRV
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.95
            },
            {
                "metric": "heart_rate",
                "value": 72,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.98
            }
        ]
    },
    {
        "device_type": "oura_ring", 
        "user_id": "test_user_001",
        "timestamp": datetime.now().isoformat(),
        "readings": [
            {
                "metric": "hrv",
                "value": 35.0,  # Low HRV - should trigger reflex mode
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.95
            },
            {
                "metric": "heart_rate",
                "value": 95,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.98
            },
            {
                "metric": "stress_level",
                "value": 0.8,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.90
            }
        ],
        "hrv_drop": 30  # Significant drop
    }
]

async def send_test_events():
    """Send test biometric events to Kafka"""
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode()
    )
    
    await producer.start()
    
    try:
        for i, event in enumerate(TEST_EVENTS):
            logger.info(f"Sending test event {i+1}: HRV={event['readings'][0]['value']}")
            await producer.send_and_wait("biometric-events", event)
            await asyncio.sleep(2)  # Wait between events
            
        logger.info("All test events sent successfully")
        
    finally:
        await producer.stop()

async def main():
    logger.info("Starting biometric bridge test...")
    logger.info("Make sure:")
    logger.info("1. Docker is running with Kafka service")
    logger.info("2. Biometric bridge is running (python -m auren.biometric.bridge)")
    logger.info("")
    
    input("Press Enter to send test events...")
    
    await send_test_events()

if __name__ == "__main__":
    asyncio.run(main()) 