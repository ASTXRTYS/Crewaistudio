import os
import json
from auren.tools.WhatsAppWebhookTool import WhatsAppWebhookTool
from auren.config.whatsapp_config import WhatsAppConfig
from auren.tools.mock_whatsapp_api import mock_whatsapp

# Set environment to development/mock
os.environ["AUREN_ENV"] = "development"

# Simulate incoming WhatsApp webhook payload
webhook_payload = json.dumps({
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
                    "wa_id": "1234567890"
                }],
                "messages": [{
                    "from": "1234567890",
                    "id": "mock_incoming_1",
                    "timestamp": "1720500000",
                    "type": "text",
                    "text": {"body": "Hello, CrewAI!"}
                }]
            },
            "field": "messages"
        }]
    }]
})

# Instantiate tool with mock config and API
tool = WhatsAppWebhookTool(config=WhatsAppConfig(mode="development"), mock_api=mock_whatsapp)

# Process the webhook
result = tool._run(webhook_payload=webhook_payload, response_message="Hi! This is CrewAI responding.")

print("=== WhatsApp Webhook Tool Result ===")
print(json.dumps(result.dict(), indent=2))

print("=== Mock WhatsApp Message History ===")
print(json.dumps(mock_whatsapp.get_message_history(), indent=2)) 