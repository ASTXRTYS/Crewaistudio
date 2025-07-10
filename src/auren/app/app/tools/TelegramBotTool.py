from typing import Optional, Dict, Any
from crewai.tools import BaseTool
import requests
import json
from pydantic import BaseModel, Field
import os


class TelegramBotToolInputSchema(BaseModel):
    action: str = Field(..., description="Action to perform: 'send_message', 'send_file', 'get_updates'")
    chat_id: Optional[str] = Field(None, description="Telegram chat ID for sending messages/files")
    message: Optional[str] = Field(None, description="Message text to send")
    file_path: Optional[str] = Field(None, description="Path to file to send")
    file_caption: Optional[str] = Field(None, description="Caption for the file")


class TelegramBotTool(BaseTool):
    name: str = "Telegram Bot"
    description: str = "Tool to interact with Telegram bot - send messages, files, and receive updates"
    args_schema = TelegramBotToolInputSchema

    def __init__(self, bot_token: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("Telegram bot token is required. Set TELEGRAM_BOT_TOKEN environment variable or pass bot_token parameter.")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def _run(self, action: str, chat_id: Optional[str] = None, message: Optional[str] = None, 
             file_path: Optional[str] = None, file_caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform Telegram bot actions
        """
        try:
            if action == "send_message":
                if not chat_id or not message:
                    return {"error": "chat_id and message are required for send_message"}
                return self._send_message(chat_id, message)
            elif action == "send_file":
                if not chat_id or not file_path:
                    return {"error": "chat_id and file_path are required for send_file"}
                return self._send_file(chat_id, file_path, file_caption)
            elif action == "get_updates":
                return self._get_updates()
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    def _send_message(self, chat_id: str, message: str) -> Dict[str, Any]:
        """Send a text message to a chat"""
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=data)
        return response.json()

    def _send_file(self, chat_id: str, file_path: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """Send a file to a chat"""
        url = f"{self.base_url}/sendDocument"
        with open(file_path, 'rb') as file:
            files = {'document': file}
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption
            response = requests.post(url, data=data, files=files)
        return response.json()

    def _get_updates(self) -> Dict[str, Any]:
        """Get recent updates from Telegram"""
        url = f"{self.base_url}/getUpdates"
        response = requests.get(url)
        return response.json()

    def run(self, input_data: TelegramBotToolInputSchema) -> Dict[str, Any]:
        return self._run(
            action=input_data.action,
            chat_id=input_data.chat_id,
            message=input_data.message,
            file_path=input_data.file_path,
            file_caption=input_data.file_caption
        ) 