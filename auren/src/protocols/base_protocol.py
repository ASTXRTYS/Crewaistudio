"""Base protocol classes for Journal, MIRAGE, and VISOR systems"""
import json
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ProtocolType(Enum):
    JOURNAL = "journal"
    MIRAGE = "mirage"
    VISOR = "visor"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class BaseProtocol(ABC):
    """Abstract base class for all protocols"""

    def __init__(self, protocol_type: ProtocolType):
        self.protocol_type = protocol_type
        self.entries = []
        self.alerts = []

    @abstractmethod
    def create_entry(self, data: Dict) -> Dict:
        """Create a new protocol entry"""
        pass

    @abstractmethod
    def analyze_trends(self, timeframe: str = "7d") -> Dict:
        """Analyze trends over specified timeframe"""
        pass

    def add_alert(self, level: AlertLevel, message: str, action: Optional[str] = None):
        """Add an alert to the protocol"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "message": message,
            "action": action,
            "protocol": self.protocol_type.value,
        }
        self.alerts.append(alert)
        return alert

    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get alerts from the last N hours"""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        return [
            alert
            for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]).timestamp() > cutoff
        ]

    def export_data(self, format: str = "json") -> str:
        """Export protocol data"""
        data = {
            "protocol": self.protocol_type.value,
            "entries": self.entries,
            "alerts": self.alerts,
            "exported_at": datetime.now().isoformat(),
        }

        if format == "json":
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
