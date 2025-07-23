"""
Health event schemas for AUREN's Kafka event pipeline.

These schemas define the structure of events flowing through the system,
ensuring type safety and consistency across all components.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    """Types of health events we track"""
    HRV_MEASUREMENT = "hrv_measurement"
    BLOOD_PRESSURE = "blood_pressure"
    GLUCOSE_READING = "glucose_reading"
    SLEEP_ANALYSIS = "sleep_analysis"
    WORKOUT_COMPLETED = "workout_completed"
    MEAL_LOGGED = "meal_logged"
    MOOD_TRACKING = "mood_tracking"
    STRESS_INDICATOR = "stress_indicator"
    BIOMETRIC_ALERT = "biometric_alert"


class TriggerType(str, Enum):
    """Types of triggers that can be detected"""
    HRV_DROP = "hrv_drop"
    BLOOD_PRESSURE_SPIKE = "blood_pressure_spike"
    GLUCOSE_SPIKE = "glucose_spike"
    SLEEP_DEPRIVATION = "sleep_deprivation"
    OVERTRAINING = "overtraining"
    STRESS_ESCALATION = "stress_escalation"
    INFLAMMATION_RISK = "inflammation_risk"
    COGNITIVE_FATIGUE = "cognitive_fatigue"


class EventPriority(str, Enum):
    """Priority levels for health events"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class BiometricMetadata(BaseModel):
    """Metadata for biometric measurements"""
    percentile_rank: Optional[float] = Field(None, ge=0.0, le=1.0)
    severity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    trend: Optional[str] = None
    statistical_summary: Optional[Dict[str, float]] = None
    timestamp_iso: str
    source_device: Optional[str] = None
    measurement_context: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    unit: Optional[str] = None


class HealthBiometricEvent(BaseModel):
    """Event for biometric measurements and health data"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    event_type: EventType
    token: str  # Unique identifier for this measurement type
    metadata: BiometricMetadata
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_json(self) -> str:
        """Convert to JSON string for Kafka"""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'HealthBiometricEvent':
        """Create from JSON string"""
        return cls.model_validate_json(json_str)


class TriggerContext(BaseModel):
    """Context for trigger detection"""
    event_sequence: List[str] = []
    time_window_hours: float = 24.0
    baseline_deviation: Optional[float] = None
    risk_factors: List[str] = []
    user_feedback: Optional[str] = None


class TriggerEvent(BaseModel):
    """Event for detected health triggers"""
    trigger_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    trigger_type: TriggerType
    severity: float = Field(..., ge=0.0, le=1.0)
    context: TriggerContext
    recommended_agents: List[str] = []
    message: str
    actionable_insights: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_json(self) -> str:
        """Convert to JSON string for Kafka"""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TriggerEvent':
        """Create from JSON string"""
        return cls.model_validate_json(json_str)


class ConversationEvent(BaseModel):
    """Event for conversation-related data"""
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    specialist_id: str
    message_type: str  # "user_input", "specialist_response", "system_message"
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_json(self) -> str:
        """Convert to JSON string for Kafka"""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ConversationEvent':
        """Create from JSON string"""
        return cls.model_validate_json(json_str)


class SystemEvent(BaseModel):
    """Event for system-level events"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    component: str
    severity: str = "info"  # "info", "warning", "error", "critical"
    message: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_json(self) -> str:
        """Convert to JSON string for Kafka"""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SystemEvent':
        """Create from JSON string"""
        return cls.model_validate_json(json_str)


class HealthEvent(BaseModel):
    """Base class for all health-related events"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventEnvelope(BaseModel):
    """Wrapper for all events with metadata"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    version: str = "1.0"
    source: str
    timestamp: datetime = Field(default_factory=datetime.now)
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    
    def to_json(self) -> str:
        """Convert to JSON string for Kafka"""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'EventEnvelope':
        """Create from JSON string"""
        return cls.model_validate_json(json_str)
