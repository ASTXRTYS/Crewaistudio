import os
import json
import hashlib
import hmac
import requests
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, ClassVar, Type
from urllib.parse import urlparse
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

# Import new config and mock API
from auren.config.whatsapp_config import WhatsAppConfig
from auren.tools.mock_whatsapp_api import mock_whatsapp

class WhatsAppWebhookInput(BaseModel):
    """Input schema for WhatsAppWebhookTool."""
    webhook_payload: str = Field(..., description="JSON string from WhatsApp webhook")
    signature_header: Optional[str] = Field(None, description="X-Hub-Signature-256 header for verification")
    response_message: Optional[str] = Field(None, description="Immediate response message to send")
    use_template: Optional[bool] = Field(False, description="Whether to use approved template for response")

class WhatsAppWebhookOutput(BaseModel):
    """Output schema for WhatsAppWebhookTool."""
    message_data: Dict[str, Any] = Field(description="Parsed message content and metadata")
    media_urls: List[str] = Field(description="Downloaded media file paths")
    delivery_status: str = Field(description="Message delivery status")
    athlete_id: str = Field(description="SHA-256 hashed athlete identifier")
    session_id: str = Field(description="Unique session identifier")

class WhatsAppWebhookTool(BaseTool):
    name: str = "WhatsApp Webhook Tool"
    description: str = "Process WhatsApp Business API webhooks with message parsing, media download, and response delivery"
    args_schema: Type[BaseModel] = WhatsAppWebhookInput
    
    _config: WhatsAppConfig = PrivateAttr()
    _mock_api: Any = PrivateAttr()
    
    def __init__(self, config: Optional[WhatsAppConfig] = None, mock_api=None, **kwargs):
        super().__init__(**kwargs)
        self._config = config or WhatsAppConfig()
        self._mock_api = mock_api or mock_whatsapp
        self._validate_environment()
        
    def _validate_environment(self):
        if not self._config.is_mock_mode():
            required_vars = ['WHATSAPP_TOKEN', 'WHATSAPP_APP_SECRET', 'WHATSAPP_PHONE_ID']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                raise EnvironmentError(
                    f"Missing required environment variables: {', '.join(missing_vars)}. "
                    f"Please set these variables before using WhatsAppWebhookTool."
                )

    def _run(
        self, 
        webhook_payload: str, 
        signature_header: Optional[str] = None,
        response_message: Optional[str] = None,
        use_template: Optional[bool] = False
    ) -> WhatsAppWebhookOutput:
        try:
            # Verify webhook signature if provided (prod only)
            if signature_header and not self._config.is_mock_mode():
                self._verify_webhook_signature(webhook_payload, signature_header)
            
            # Parse incoming webhook data
            message_data = self._parse_webhook_data(webhook_payload)
            
            # Generate session and athlete IDs
            session_id = str(uuid.uuid4())
            athlete_id = self._hash_phone_number(message_data.get('from_number', ''))
            
            # Download any media attachments
            media_urls = []
            if message_data.get('media'):
                media_urls = self._download_media_attachments(message_data['media'])
            
            # Send immediate response if provided
            delivery_status = "none"
            if response_message and message_data.get('from_number'):
                delivery_status = self._send_whatsapp_message(
                    message_data['from_number'],
                    response_message,
                    use_template or False
                )
            
            return WhatsAppWebhookOutput(
                message_data=message_data,
                media_urls=media_urls,
                delivery_status=delivery_status,
                athlete_id=athlete_id,
                session_id=session_id
            )
            
        except Exception as e:
            return WhatsAppWebhookOutput(
                message_data={},
                media_urls=[],
                delivery_status=f"error: {str(e)}",
                athlete_id="",
                session_id=str(uuid.uuid4())
            )

    def _verify_webhook_signature(self, payload: str, signature_header: str) -> None:
        app_secret = self._config.app_secret
        if not app_secret:
            raise ValueError("WHATSAPP_APP_SECRET environment variable not set")
        signature = signature_header.replace('sha256=', '')
        expected_signature = hmac.new(
            app_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid webhook signature")

    def _parse_webhook_data(self, webhook_payload: str) -> Dict[str, Any]:
        try:
            data = json.loads(webhook_payload)
            if 'hub.challenge' in data:
                return {
                    'webhook_verification': True,
                    'challenge': data['hub.challenge'],
                    'from_number': None,
                    'message_type': 'verification',
                    'text': None,
                    'media': [],
                    'timestamp': datetime.utcnow().isoformat(),
                    'raw_payload': data
                }
            if 'entry' not in data or not data['entry']:
                return self._empty_message_data(data)
            entry = data['entry'][0]
            if 'changes' not in entry or not entry['changes']:
                return self._empty_message_data(data)
            change = entry['changes'][0]
            if change.get('field') != 'messages' or 'value' not in change:
                return self._empty_message_data(data)
            value = change['value']
            if 'messages' in value and value['messages']:
                return self._parse_message(value['messages'][0], data)
            elif 'statuses' in value:
                return self._parse_status(value['statuses'][0], data)
            else:
                return self._empty_message_data(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON payload: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse webhook data: {str(e)}")

    def _parse_message(self, message: Dict[str, Any], raw_data: Dict[str, Any]) -> Dict[str, Any]:
        message_type = message.get('type', 'unknown')
        from_number = message.get('from', '')
        timestamp = message.get('timestamp', str(int(datetime.utcnow().timestamp())))
        text_content = None
        if message_type == 'text' and 'text' in message:
            text_content = message['text'].get('body', '')
        media_list = []
        if message_type in ['image', 'video', 'audio', 'document']:
            media_info = message.get(message_type, {})
            if 'id' in media_info:
                media_list.append({
                    'id': media_info['id'],
                    'type': message_type,
                    'mime_type': media_info.get('mime_type', ''),
                    'caption': media_info.get('caption', ''),
                    'filename': media_info.get('filename', '')
                })
        return {
            'from_number': from_number,
            'message_type': message_type,
            'text': text_content,
            'media': media_list,
            'timestamp': timestamp,
            'raw_payload': raw_data,
            'message_id': message.get('id', ''),
            'webhook_verification': False
        }

    def _parse_status(self, status: Dict[str, Any], raw_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'from_number': status.get('recipient_id', ''),
            'message_type': 'status',
            'text': None,
            'media': [],
            'timestamp': str(int(datetime.utcnow().timestamp())),
            'raw_payload': raw_data,
            'status': status.get('status', ''),
            'message_id': status.get('id', ''),
            'webhook_verification': False
        }

    def _empty_message_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'from_number': None,
            'message_type': 'unknown',
            'text': None,
            'media': [],
            'timestamp': datetime.utcnow().isoformat(),
            'raw_payload': raw_data,
            'webhook_verification': False
        }

    def _download_media_attachments(self, media_list: List[Dict[str, Any]]) -> List[str]:
        if self._config.is_mock_mode():
            # In mock mode, just return fake file paths
            return [f"/tmp/mock_{m['id']}.bin" for m in media_list if 'id' in m]
        downloaded_files = []
        token = self._config.token
        for media_item in media_list:
            try:
                media_id = media_item.get('id')
                if not media_id:
                    continue
                url_response = requests.get(
                    f"https://graph.facebook.com/v19.0/{media_id}",
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=10
                )
                if url_response.status_code != 200:
                    continue
                media_url_data = url_response.json()
                media_url = media_url_data.get('url')
                if not media_url:
                    continue
                media_response = requests.get(
                    media_url,
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=30
                )
                if media_response.status_code == 200:
                    mime_type = media_item.get('mime_type', '')
                    file_ext = self._get_file_extension(mime_type, media_item.get('type', ''))
                    filename = f"{media_id}_{int(datetime.utcnow().timestamp())}{file_ext}"
                    file_path = f"/tmp/{filename}"
                    with open(file_path, 'wb') as f:
                        f.write(media_response.content)
                    downloaded_files.append(file_path)
            except Exception as e:
                print(f"Failed to download media {media_item.get('id', 'unknown')}: {str(e)}")
                continue
        return downloaded_files

    def _get_file_extension(self, mime_type: str, media_type: str) -> str:
        mime_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'video/mp4': '.mp4',
            'video/quicktime': '.mov',
            'audio/mpeg': '.mp3',
            'audio/ogg': '.ogg',
            'audio/wav': '.wav',
            'application/pdf': '.pdf'
        }
        if mime_type in mime_map:
            return mime_map[mime_type]
        type_map = {
            'image': '.jpg',
            'video': '.mp4',
            'audio': '.mp3',
            'document': '.pdf'
        }
        return type_map.get(media_type, '.bin')

    def _send_whatsapp_message(
        self, 
        to_number: str, 
        message: str, 
        use_template: bool = False
    ) -> str:
        if self._config.is_mock_mode():
            # Use mock API for sending messages
            resp = self._mock_api.send_message(to_number, message, "text")
            return f"mock_sent:{resp['messages'][0]['id']}"
        try:
            phone_id = self._config.phone_id
            token = self._config.token
            url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            if use_template:
                payload = {
                    'messaging_product': 'whatsapp',
                    'to': to_number,
                    'type': 'text',
                    'text': {'body': message}
                }
            else:
                payload = {
                    'messaging_product': 'whatsapp',
                    'to': to_number,
                    'type': 'text',
                    'text': {'body': message}
                }
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get('messages', [{}])[0].get('id', '')
                return f"sent:{message_id}"
            else:
                return f"failed:{response.status_code}:{response.text[:100]}"
        except Exception as e:
            return f"error:{str(e)}"

    def _hash_phone_number(self, phone_number: str) -> str:
        if not phone_number:
            return ""
        normalized = ''.join(filter(str.isdigit, phone_number))
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def handle_webhook_verification(self, hub_mode: str, hub_challenge: str, hub_verify_token: str) -> str:
        verify_token = self._config.token  # Use config for verify token
        if hub_mode == 'subscribe' and hub_verify_token == verify_token:
            return hub_challenge
        else:
            raise ValueError("Invalid verification token") 