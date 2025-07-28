"""
AUREN Biometric Bridge Type Definitions
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, TypedDict, Dict, Any
from datetime import datetime


class WearableType(str, Enum):
    """Supported wearable device types"""
    APPLE_HEALTH = "apple_health"
    OURA = "oura"
    WHOOP = "whoop"
    GARMIN = "garmin"


@dataclass
class BiometricReading:
    """Individual biometric reading with metadata"""
    metric: str
    value: float
    timestamp: datetime
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validate reading on creation"""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if self.value < 0 and self.metric not in ["temperature_deviation"]:
            raise ValueError(f"Biometric value cannot be negative: {self.metric}")


@dataclass
class BiometricEvent:
    """Collection of biometric readings from a device"""
    device_type: WearableType
    user_id: str
    timestamp: datetime
    readings: List[BiometricReading]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "device_type": self.device_type.value,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "readings": [
                {
                    "metric": r.metric,
                    "value": r.value,
                    "timestamp": r.timestamp.isoformat(),
                    "confidence": r.confidence
                } for r in self.readings
            ]
        }


class CognitiveMode(str, Enum):
    """Cognitive operation modes based on biometric state"""
    REFLEX = "reflex"       # High stress, immediate response needed
    PATTERN = "pattern"     # Normal operation, pattern recognition
    HYPOTHESIS = "hypothesis"  # Exploration mode for anomalies
    GUARDIAN = "guardian"   # Low energy, protective mode


class NEUROSState(TypedDict):
    """Complete state for NEUROS cognitive agent"""
    # Messages and conversation state
    messages: List[Any]  # List of LangChain messages
    
    # Cognitive mode information
    current_mode: CognitiveMode
    previous_mode: Optional[CognitiveMode]
    mode_confidence: float
    mode_history: List[dict]
    
    # Biometric data
    latest_biometric_event: Optional[dict]
    hrv_current: Optional[float]
    hrv_baseline: Optional[float]
    hrv_drop: Optional[float]
    heart_rate: Optional[float]
    stress_level: Optional[float]
    recovery_score: Optional[float]
    
    # Session information
    user_id: str
    session_id: str
    
    # Trigger information
    last_biometric_trigger: Optional[str]
    trigger_timestamp: Optional[str]
    
    # Hypothesis and pattern tracking
    active_hypothesis: Optional[str]
    pattern_detections: List[str]
    
    # Checkpoint management
    checkpoint_id: Optional[str]
    last_checkpoint: Optional[str]
    checkpoint_version: int
    
    # Error handling
    error_count: int
    last_error: Optional[str]
    
    # Concurrency control
    processing_lock: bool
    parallel_tasks: List[str] 