#!/usr/bin/env python3
"""
Simplified infrastructure validation for AUREN Kafka setup.

This script provides a quick validation of the Kafka infrastructure
without requiring all services to be running.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from kafka import KafkaAdminClient
from kafka.errors import KafkaError
from datetime import datetime


def check_kafka_connectivity():
    """Check if Kafka is accessible"""
    try:
        admin = KafkaAdminClient(
            bootstrap_servers="localhost:9092",
            client_id='validation-check',
            request_timeout_ms=5000
        )
        
        # Test basic connectivity
        topics = admin.list_topics()
        admin.close()
        
        return True, f"Kafka accessible with {len(topics)} topics"
        
    except KafkaError as e:
        return False, f"Kafka error: {str(e)}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def check_required_topics():
    """Check if required topics exist"""
    try:
        admin = KafkaAdminClient(
            bootstrap_servers="localhost:9092",
            client_id='validation-check',
            request_timeout_ms=5000
        )
        
        existing_topics = admin.list_topics()
        admin.close()
        
        # Check for our required topics
        required_topics = [
            "health-events",
            "biometric-updates", 
            "alerts",
            "milestones"
        ]
        
        missing_topics = []
        for topic in required_topics:
            if topic not in existing_topics:
                missing_topics.append(topic)
        
        if not missing_topics:
            return True, "All required topics exist"
        else:
            return False, f"Missing topics: {missing_topics}"
            
    except Exception as e:
        return False, f"Topic check failed: {str(e)}"


def validate_infrastructure():
    """Complete infrastructure validation"""
    print("=" * 60)
    print("AUREN Kafka Infrastructure Validation")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check Kafka connectivity
    print("🔍 Checking Kafka connectivity...")
    kafka_ok, kafka_msg = check_kafka_connectivity()
    print(f"   {'✅' if kafka_ok else '❌'} {kafka_msg}")
    
    # Check required topics
    print("🔍 Checking required topics...")
    topics_ok, topics_msg = check_required_topics()
    print(f"   {'✅' if topics_ok else '❌'} {topics_msg}")
    
    # Overall status
    print()
    print("=" * 60)
    print("VALIDATION RESULT")
    print("=" * 60)
    
    if kafka_ok and topics_ok:
        print("🎉 INFRASTRUCTURE READY FOR CEP!")
        print("✅ Kafka cluster accessible")
        print("✅ All required topics exist")
        print("✅ Ready for Flink CEP implementation")
        return True
    else:
        print("⚠️  Infrastructure needs attention")
        if not kafka_ok:
            print("   - Ensure Kafka is running on localhost:9092")
            print("   - Check docker-compose services")
        if not topics_ok:
            print("   - Run topic creation script")
            print("   - Check topic configuration")
        return False


def create_topics_if_needed():
    """Create required topics if they don't exist"""
    try:
        from src.infrastructure.kafka.topics import TopicManager
        
        print("🔄 Creating required topics...")
        manager = TopicManager()
        manager.create_topics()
        print("✅ Topics created successfully")
        
    except Exception as e:
        print(f"❌ Failed to create topics: {e}")


if __name__ == "__main__":
    print("AUREN Kafka Infrastructure Validation")
    print("=" * 60)
    
    # Validate current state
    ready = validate_infrastructure()
    
    if not ready:
        print()
        print("💡 Suggested actions:")
        print("1. Start services: docker-compose up -d")
        print("2. Create topics: python -c 'from src.infrastructure.kafka.topics import TopicManager; TopicManager().create_topics()'")
        print("3. Re-run validation")
    
    sys.exit(0 if ready else 1)
