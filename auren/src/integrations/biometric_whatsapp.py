"""WhatsApp integration with biometric protocol awareness"""
import asyncio
import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of WhatsApp messages"""

    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    VOICE = "audio"
    LOCATION = "location"


class BiometricWhatsAppConnector:
    """Enhanced WhatsApp connector for biometric updates"""

    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_id = os.getenv("WHATSAPP_PHONE_ID")
        self.business_id = os.getenv("WHATSAPP_BUSINESS_ID")
        self.api_version = os.getenv("WHATSAPP_API_VERSION", "v18.0")
        self.webhook_token = os.getenv("WHATSAPP_WEBHOOK_TOKEN")

        if not all([self.access_token, self.phone_id]):
            raise ValueError("Missing WhatsApp credentials in environment")

        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        # Message templates for biometric updates
        self.templates = {
            "daily_reminder": "🌟 Good morning! Time for your daily biometric check-in. Please send your morning photos when ready.",
            "ptosis_alert": "⚠️ Ptosis Alert: Your recent scores indicate elevated ptosis ({score}). Implementing recovery protocol.",
            "positive_milestone": "🎉 Fantastic progress! Your biometric scores are showing excellent improvement!",
            "weekly_report": "📊 Your weekly biometric report is ready. Let me share your insights...",
        }

    async def send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send text message with correct payload structure."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }

        return await self._make_request("POST", "messages", payload)

    async def send_message(
        self, to_number: str, message: str, message_type: MessageType = MessageType.TEXT
    ) -> Dict[str, Any]:
        """Send message via WhatsApp"""

        if message_type == MessageType.TEXT:
            return await self.send_text_message(to_number, message)
        else:
            # Handle other message types
            payload = self._build_media_payload(to_number, message, message_type)
            return await self._make_request("POST", "messages", payload)

    def _build_media_payload(
        self, to_number: str, media_id: str, message_type: MessageType
    ) -> Dict:
        """Build payload for media messages"""

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": message_type.value,
        }

        if message_type == MessageType.IMAGE:
            payload["image"] = {"id": media_id}
        elif message_type == MessageType.DOCUMENT:
            payload["document"] = {"id": media_id}
        elif message_type == MessageType.VOICE:
            payload["audio"] = {"id": media_id}

        return payload

    async def send_interactive_buttons(
        self, to_number: str, body_text: str, buttons: List[Dict]
    ) -> Dict:
        """Send interactive button message with proper structure."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": str(btn["id"]),
                                "title": str(btn["title"])[:20],  # WhatsApp limit
                            },
                        }
                        for btn in buttons
                    ]
                },
            },
        }

        return await self._make_request("POST", "messages", payload)

    async def send_list_message(
        self, to_number: str, header: str, body: str, sections: List[Dict]
    ) -> Dict:
        """Send list selection message"""

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": header},
                "body": {"text": body},
                "action": {"button": "Select Option", "sections": sections},
            },
        }

        return await self._make_request("POST", "messages", payload)

    async def _make_request(self, method: str, endpoint: str, payload: Dict) -> Dict[str, Any]:
        """Make HTTP request to WhatsApp API"""
        url = f"{self.base_url}/{self.phone_id}/{endpoint}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method, url, headers=self.headers, json=payload, timeout=30.0
                )

                response.raise_for_status()
                result = response.json()

                logger.info(f"WhatsApp API {method} {endpoint}: {result}")
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API error: {e.response.text}")
            return {"error": str(e), "details": e.response.text}
        except Exception as e:
            logger.error(f"Failed to make WhatsApp request: {str(e)}")
            return {"error": str(e)}

    def extract_message_data(self, webhook_body: Dict) -> Optional[Dict]:
        """Extract and categorize message data from webhook"""

        try:
            entry = webhook_body.get("entry", [])
            if not entry:
                return None

            changes = entry[0].get("changes", [])
            if not changes:
                return None

            value = changes[0].get("value", {})
            messages = value.get("messages", [])

            if not messages:
                return None

            message = messages[0]

            # Extract base fields
            extracted = {
                "from": message.get("from"),
                "id": message.get("id"),
                "timestamp": message.get("timestamp"),
                "type": message.get("type"),
                "context": message.get("context"),
            }

            # Extract type-specific data
            if message["type"] == "text":
                extracted["text"] = message.get("text", {}).get("body")
                extracted["intent"] = self._detect_message_intent(extracted["text"])

            elif message["type"] == "image":
                extracted["image"] = message.get("image", {})
                extracted["caption"] = message.get("image", {}).get("caption", "")
                extracted["intent"] = "biometric_photo"

            elif message["type"] == "interactive":
                if message.get("interactive", {}).get("type") == "button_reply":
                    extracted["button_id"] = message["interactive"]["button_reply"]["id"]
                    extracted["button_title"] = message["interactive"]["button_reply"]["title"]
                elif message.get("interactive", {}).get("type") == "list_reply":
                    extracted["list_id"] = message["interactive"]["list_reply"]["id"]
                    extracted["list_title"] = message["interactive"]["list_reply"]["title"]

            return extracted

        except Exception as e:
            logger.error(f"Failed to extract message: {str(e)}")
            return None

    def _detect_message_intent(self, text: str) -> str:
        """Detect intent from message text"""

        if not text:
            return "unknown"

        text_lower = text.lower()

        # Biometric-specific intents
        if any(word in text_lower for word in ["weight", "weigh", "scale"]):
            return "weight_log"
        elif any(word in text_lower for word in ["photo", "pic", "image", "face"]):
            return "photo_request"
        elif any(word in text_lower for word in ["peptide", "dose", "inject", "compound"]):
            return "peptide_log"
        elif any(word in text_lower for word in ["meal", "ate", "food", "calories", "macros"]):
            return "nutrition_log"
        elif any(word in text_lower for word in ["sleep", "slept", "tired", "fatigue"]):
            return "sleep_log"
        elif any(word in text_lower for word in ["workout", "training", "exercise", "gym"]):
            return "training_log"
        elif any(word in text_lower for word in ["report", "summary", "analysis", "progress"]):
            return "report_request"
        elif any(word in text_lower for word in ["help", "commands", "what can"]):
            return "help_request"
        else:
            return "general_chat"

    async def download_media(self, media_id: str) -> Optional[bytes]:
        """Download media file from WhatsApp"""

        # First, get the download URL
        url = f"{self.base_url}/{media_id}"

        try:
            async with httpx.AsyncClient() as client:
                # Get media URL
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                media_data = response.json()

                download_url = media_data.get("url")
                if not download_url:
                    return None

                # Download the actual media
                response = await client.get(download_url, headers=self.headers)
                response.raise_for_status()

                return response.content

        except Exception as e:
            logger.error(f"Failed to download media: {e}")
            return None

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read"""

        payload = {"messaging_product": "whatsapp", "status": "read", "message_id": message_id}

        try:
            result = await self._make_request("POST", "messages", payload)
            return "error" not in result
        except Exception as e:
            logger.error(f"Failed to mark as read: {str(e)}")
            return False

    async def send_biometric_reminder(self, to_number: str, reminder_type: str = "daily") -> Dict:
        """Send biometric check-in reminder"""

        if reminder_type == "daily":
            buttons = [
                {"type": "reply", "reply": {"id": "ready_photos", "title": "📸 Ready"}},
                {"type": "reply", "reply": {"id": "snooze_30", "title": "⏰ 30 min"}},
                {"type": "reply", "reply": {"id": "skip_today", "title": "Skip today"}},
            ]

            return await self.send_interactive_buttons(
                to_number, self.templates["daily_reminder"], buttons
            )

        return {"status": "unknown_reminder_type"}

    async def send_protocol_menu(self, to_number: str) -> Dict:
        """Send protocol selection menu"""

        sections = [
            {
                "title": "Log Entry",
                "rows": [
                    {"id": "log_weight", "title": "⚖️ Weight", "description": "Log morning weight"},
                    {"id": "log_peptide", "title": "💉 Peptide", "description": "Log peptide dose"},
                    {
                        "id": "log_macros",
                        "title": "🍽️ Nutrition",
                        "description": "Log meals/macros",
                    },
                    {"id": "log_sleep", "title": "😴 Sleep", "description": "Log sleep quality"},
                ],
            },
            {
                "title": "Reports",
                "rows": [
                    {
                        "id": "report_daily",
                        "title": "📊 Daily Report",
                        "description": "Today's summary",
                    },
                    {
                        "id": "report_weekly",
                        "title": "📈 Weekly Report",
                        "description": "7-day analysis",
                    },
                    {
                        "id": "report_alerts",
                        "title": "⚠️ Active Alerts",
                        "description": "Current warnings",
                    },
                ],
            },
            {
                "title": "Protocols",
                "rows": [
                    {
                        "id": "protocol_journal",
                        "title": "📖 Journal",
                        "description": "Peptide protocol",
                    },
                    {
                        "id": "protocol_mirage",
                        "title": "🔮 MIRAGE",
                        "description": "Visual analysis",
                    },
                    {
                        "id": "protocol_convergence",
                        "title": "🔄 Convergence",
                        "description": "Cross-analysis",
                    },
                ],
            },
        ]

        return await self.send_list_message(
            to_number, "AUREN Menu", "What would you like to do?", sections
        )

    def format_biometric_scores(self, scores: Dict) -> str:
        """Format biometric scores for WhatsApp"""

        # Use emojis for visual appeal
        inflammation_emoji = (
            "🟢"
            if scores.get("inflammation", 0) < 2
            else "🟡"
            if scores.get("inflammation", 0) < 3
            else "🔴"
        )
        ptosis_emoji = (
            "🟢" if scores.get("ptosis", 0) < 4 else "🟡" if scores.get("ptosis", 0) < 6.5 else "🔴"
        )

        return f"""📊 *Biometric Analysis*

{inflammation_emoji} Inflammation: {scores.get('inflammation', 0)}/5
{ptosis_emoji} Ptosis: {scores.get('ptosis', 0)}/10
🔄 Symmetry: {scores.get('symmetry', 0)}/5
💧 Lymphatic: {scores.get('lymphatic_fullness', 0)}/5
✨ Skin Clarity: {scores.get('skin_clarity', 0)}/5

_Analysis complete at {datetime.now().strftime('%I:%M %p')}_"""

    def format_alert(self, alert: Dict) -> str:
        """Format alert for WhatsApp"""

        severity_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}

        emoji = severity_emoji.get(alert.get("severity", "info"), "📌")

        message = f"{emoji} *{alert.get('severity', '').upper()} ALERT*\n\n"
        message += f"{alert.get('message', '')}\n"

        if alert.get("action"):
            message += f"\n*Recommended Action:*\n{alert['action'].replace('_', ' ').title()}"

        return message
