"""Mock WhatsApp interface for testing without Twilio dependency"""
import asyncio
import json
from typing import Dict


class MockWhatsAppInterface:
    def __init__(self):
        self.message_log = []

    async def send_message(self, phone_number: str, message: str) -> Dict:
        """Simulate sending WhatsApp message"""
        self.message_log.append({"to": phone_number, "message": message, "status": "sent"})
        print(f"[MOCK WhatsApp] To {phone_number}: {message}")
        return {"success": True, "message_id": f"mock_{len(self.message_log)}"}

    async def receive_message(self, phone_number: str, message: str) -> Dict:
        """Simulate receiving WhatsApp message"""
        print(f"[MOCK WhatsApp] From {phone_number}: {message}")
        return {"from": phone_number, "message": message}
