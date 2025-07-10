import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, ClassVar, Type
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class JSONLoggerInput(BaseModel):
    """Input schema for JSONLoggerTool."""
    data: Dict[str, Any] = Field(..., description="Data to log as JSON")
    log_file: Optional[str] = Field(None, description="Custom log file path (optional)")
    session_id: Optional[str] = Field(None, description="Session identifier")
    log_level: Optional[str] = Field("INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")


class JSONLoggerOutput(BaseModel):
    """Output schema for JSONLoggerTool."""
    logged: bool = Field(description="Whether the data was successfully logged")
    log_entry_id: str = Field(description="Unique identifier for the log entry")
    log_file_path: str = Field(description="Path to the log file")
    timestamp: str = Field(description="Timestamp of the log entry")


class JSONLoggerTool(BaseTool):
    name: str = "JSON Logger Tool"
    description: str = "Log structured data to JSON files with timestamps and session tracking"
    args_schema: Type[BaseModel] = JSONLoggerInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.default_log_dir = "logs"
        self._ensure_log_directory()
        
    def _ensure_log_directory(self):
        """Ensure the log directory exists."""
        Path(self.default_log_dir).mkdir(parents=True, exist_ok=True)

    def _run(
        self, 
        data: Dict[str, Any], 
        log_file: Optional[str] = None,
        session_id: Optional[str] = None,
        log_level: Optional[str] = "INFO"
    ) -> JSONLoggerOutput:
        """Log structured data to JSON file."""
        try:
            # Generate unique entry ID
            entry_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            # Determine log file path
            if log_file:
                log_file_path = log_file
            else:
                # Default log file based on current date
                date_str = datetime.utcnow().strftime("%Y-%m-%d")
                log_file_path = os.path.join(self.default_log_dir, f"app_log_{date_str}.json")
            
            # Ensure log file directory exists
            Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Create log entry
            log_entry = {
                "entry_id": entry_id,
                "timestamp": timestamp,
                "session_id": session_id,
                "log_level": log_level,
                "data": data
            }
            
            # Read existing logs or create new list
            existing_logs = []
            if os.path.exists(log_file_path):
                try:
                    with open(log_file_path, 'r', encoding='utf-8') as f:
                        existing_logs = json.load(f)
                    if not isinstance(existing_logs, list):
                        existing_logs = []
                except (json.JSONDecodeError, IOError):
                    existing_logs = []
            
            # Append new log entry
            existing_logs.append(log_entry)
            
            # Write back to file
            with open(log_file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_logs, f, indent=2, ensure_ascii=False)
            
            return JSONLoggerOutput(
                logged=True,
                log_entry_id=entry_id,
                log_file_path=log_file_path,
                timestamp=timestamp
            )
            
        except Exception as e:
            # Return error result
            return JSONLoggerOutput(
                logged=False,
                log_entry_id="",
                log_file_path=log_file or "unknown",
                timestamp=datetime.utcnow().isoformat()
            )

    def get_logs(self, log_file: Optional[str] = None, session_id: Optional[str] = None) -> list:
        """Retrieve logs from file, optionally filtered by session."""
        try:
            if log_file:
                log_file_path = log_file
            else:
                date_str = datetime.utcnow().strftime("%Y-%m-%d")
                log_file_path = os.path.join(self.default_log_dir, f"app_log_{date_str}.json")
            
            if not os.path.exists(log_file_path):
                return []
            
            with open(log_file_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            if not isinstance(logs, list):
                return []
            
            # Filter by session_id if provided
            if session_id:
                logs = [log for log in logs if log.get('session_id') == session_id]
            
            return logs
            
        except Exception:
            return []

    def clear_logs(self, log_file: Optional[str] = None) -> bool:
        """Clear all logs from specified file."""
        try:
            if log_file:
                log_file_path = log_file
            else:
                date_str = datetime.utcnow().strftime("%Y-%m-%d")
                log_file_path = os.path.join(self.default_log_dir, f"app_log_{date_str}.json")
            
            if os.path.exists(log_file_path):
                os.remove(log_file_path)
            
            return True
            
        except Exception:
            return False 