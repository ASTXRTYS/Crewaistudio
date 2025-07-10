"""Mock WhatsApp API for development and testing"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MockWhatsAppAPI:
    """Mock WhatsApp API for development"""
    
    def __init__(self):
        self.messages_sent = []
        self.webhook_events = []
        self.verify_token = "auren_verify_token"
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify webhook challenge"""
        if mode == "subscribe" and token == self.verify_token:
            logger.info("Webhook verification successful")
            return challenge
        return None
    
    def send_message(self, phone_number: str, message: str, message_type: str = "text") -> Dict[str, Any]:
        """Mock sending a WhatsApp message"""
        message_id = f"mock_msg_{len(self.messages_sent) + 1}"
        
        mock_response = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": phone_number, "wa_id": phone_number}],
            "messages": [{"id": message_id}]
        }
        
        # Log the message
        self.messages_sent.append({
            "id": message_id,
            "to": phone_number,
            "message": message,
            "type": message_type,
            "timestamp": datetime.now().isoformat(),
            "status": "sent"
        })
        
        logger.info(f"Mock WhatsApp message sent: {message_id} to {phone_number}")
        return mock_response
    
    def get_message_history(self) -> list:
        """Get sent message history"""
        return self.messages_sent
    
    def simulate_incoming_message(self, from_number: str, message_text: str, message_type: str = "text") -> Dict[str, Any]:
        """Simulate an incoming WhatsApp message"""
        event = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "mock_phone_id",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "mock_phone_id"
                        },
                        "contacts": [{
                            "profile": {"name": "Test User"},
                            "wa_id": from_number
                        }],
                        "messages": [{
                            "from": from_number,
                            "id": f"mock_incoming_{len(self.webhook_events) + 1}",
                            "timestamp": str(int(datetime.now().timestamp())),
                            "type": message_type,
                            "text": {"body": message_text}
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        self.webhook_events.append(event)
        logger.info(f"Simulated incoming message: {message_text} from {from_number}")
        return event
    
    def get_webhook_events(self) -> list:
        """Get webhook event history"""
        return self.webhook_events

# Global mock instance
mock_whatsapp = MockWhatsAppAPI() 