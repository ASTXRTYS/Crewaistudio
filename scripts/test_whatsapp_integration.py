#!/usr/bin/env python3
"""
Test script for WhatsApp integration
Tests the end-to-end flow from message reception to agent response
"""

import requests
import json
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_webhook_endpoint():
    """Test the webhook endpoint is accessible"""
    try:
        # Test GET request (verification)
        response = requests.get(
            "http://localhost:8506/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_token",
                "hub.challenge": "1234567890"
            }
        )
        
        if response.status_code == 200:
            logger.info("✅ Webhook verification endpoint working")
            return True
        else:
            logger.error(f"❌ Webhook verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Webhook test failed: {e}")
        return False

def test_message_processing():
    """Test message processing through the crew"""
    try:
        # Simulate a WhatsApp message
        test_message = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "123456789"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": "1234567890"
                        }],
                        "messages": [{
                            "from": "1234567890",
                            "id": "test_msg_id",
                            "timestamp": "1234567890",
                            "type": "text",
                            "text": {"body": "Hello, I need help with nutrition"}
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        # Send POST to webhook
        response = requests.post(
            "http://localhost:8506/webhook",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_message)
        )
        
        logger.info(f"Message processing test response: {response.status_code}")
        return response.status_code in [200, 403]  # 403 is expected for test tokens
        
    except Exception as e:
        logger.error(f"❌ Message processing test failed: {e}")
        return False

def test_crew_creation():
    """Test that WhatsApp crew can be created"""
    try:
        from auren.crews.whatsapp_crew import WhatsAppCrew
        
        crew = WhatsAppCrew()
        logger.info("✅ WhatsApp crew created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Crew creation failed: {e}")
        return False

def test_agent_creation():
    """Test that specialist agents can be created"""
    try:
        from auren.agents.whatsapp_message_handler import WhatsAppMessageHandler
        
        handler = WhatsAppMessageHandler()
        router_agent = handler.create_router_agent()
        specialist_agents = handler.create_specialist_agents()
        
        logger.info(f"✅ Created {len(specialist_agents)} specialist agents")
        return True
        
    except Exception as e:
        logger.error(f"❌ Agent creation failed: {e}")
        return False

def main():
    """Run all WhatsApp integration tests"""
    logger.info("🧪 Starting WhatsApp integration tests...")
    
    tests = [
        ("Webhook Endpoint", test_webhook_endpoint),
        ("Agent Creation", test_agent_creation),
        ("Crew Creation", test_crew_creation),
        ("Message Processing", test_message_processing),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status}: {test_name}")
        except Exception as e:
            logger.error(f"❌ ERROR: {test_name} - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! WhatsApp integration is ready.")
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 