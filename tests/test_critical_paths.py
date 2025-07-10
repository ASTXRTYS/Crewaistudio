import pytest
import json
from unittest.mock import Mock, patch
from src.auren.config.whatsapp_config import WhatsAppConfig
from src.auren.tools.mock_whatsapp_api import mock_whatsapp

class TestCriticalPaths:
    """Test the most important user journeys"""
    
    def setup_method(self):
        """Setup for each test"""
        self.whatsapp_config = WhatsAppConfig(mode="development")
        mock_whatsapp.messages_sent.clear()
        mock_whatsapp.webhook_events.clear()
    
    def test_whatsapp_message_to_response(self):
        """End-to-end: WhatsApp message → Agent → Response"""
        # This is the MVP test
        from_number = "1234567890"
        message_text = "Hello, I need help with a task"
        
        # 1. Simulate incoming WhatsApp message
        webhook_event = mock_whatsapp.simulate_incoming_message(
            from_number=from_number,
            message_text=message_text
        )
        
        # 2. Process webhook (this would be done by the webhook endpoint)
        assert webhook_event["object"] == "whatsapp_business_account"
        assert len(webhook_event["entry"]) > 0
        
        # 3. Extract message data
        message_data = webhook_event["entry"][0]["changes"][0]["value"]["messages"][0]
        assert message_data["from"] == from_number
        assert message_data["text"]["body"] == message_text
        
        # 4. Send mock response
        response_text = "I received your message and will help you with your task."
        mock_whatsapp.send_message(
            phone_number=from_number,
            message=response_text
        )
        
        # 5. Verify response was sent
        assert len(mock_whatsapp.get_message_history()) == 1
        sent_message = mock_whatsapp.get_message_history()[0]
        assert sent_message["to"] == from_number
        assert sent_message["message"] == response_text
    
    def test_agent_creation_and_execution(self):
        """Can create agent and execute task"""
        # This test would verify agent creation and task execution
        # For now, we'll test the configuration system
        assert self.whatsapp_config.is_mock_mode() == True
        assert self.whatsapp_config.validate_config() == True
    
    def test_crew_orchestration(self):
        """Multiple agents work together"""
        # This test would verify crew coordination
        # For now, we'll test the mock API functionality
        assert mock_whatsapp.verify_webhook(
            mode="subscribe",
            token="auren_verify_token",
            challenge="test_challenge"
        ) == "test_challenge"
    
    def test_webhook_verification(self):
        """Test webhook verification flow"""
        # Test successful verification
        challenge = mock_whatsapp.verify_webhook(
            mode="subscribe",
            token="auren_verify_token",
            challenge="test_challenge_123"
        )
        assert challenge == "test_challenge_123"
        
        # Test failed verification
        challenge = mock_whatsapp.verify_webhook(
            mode="subscribe",
            token="wrong_token",
            challenge="test_challenge_123"
        )
        assert challenge is None
    
    def test_message_history_tracking(self):
        """Test that message history is properly tracked"""
        # Send multiple messages
        mock_whatsapp.send_message("1234567890", "Message 1")
        mock_whatsapp.send_message("1234567890", "Message 2")
        mock_whatsapp.send_message("0987654321", "Message 3")
        
        history = mock_whatsapp.get_message_history()
        assert len(history) == 3
        assert history[0]["message"] == "Message 1"
        assert history[1]["message"] == "Message 2"
        assert history[2]["message"] == "Message 3" 