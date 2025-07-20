"""
Topic configuration and mapping for AUREN Kafka infrastructure.

Provides mapping between logical topic names (original specification) and actual topic names (current implementation).
This allows us to maintain descriptive names while ensuring compatibility with CEP requirements.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum


class EventType(Enum):
    """Event types for topic routing"""
    BIOMETRIC = "biometric"
    TRIGGER = "trigger"
    CONVERSATION = "conversation"
    MILESTONE = "milestone"
    ALERT = "alert"


@dataclass
class TopicMapping:
    """Maps between logical topic names and actual Kafka topic names"""
    
    # Original specification names (logical)
    HEALTH_BIOMETRICS = "health.biometrics"
    TRIGGERS_DETECTED = "triggers.detected"
    CONVERSATIONS_EVENTS = "conversations.events"
    
    # Current implementation names (actual/descriptive)
    HEALTH_EVENTS = "health-events"
    ALERTS = "alerts"
    BIOMETRIC_UPDATES = "biometric-updates"
    MILESTONES = "milestones"
    
    @classmethod
    def get_mapping(cls) -> Dict[str, str]:
        """Returns mapping from logical to actual topic names"""
        return {
            cls.HEALTH_BIOMETRICS: cls.BIOMETRIC_UPDATES,
            cls.TRIGGERS_DETECTED: cls.ALERTS,
            cls.CONVERSATIONS_EVENTS: cls.HEALTH_EVENTS,
        }
    
    @classmethod
    def get_topic_for_event_type(cls, event_type: EventType) -> str:
        """Returns the appropriate topic for a given event type"""
        mapping = {
            EventType.BIOMETRIC: cls.BIOMETRIC_UPDATES,
            EventType.TRIGGER: cls.ALERTS,
            EventType.CONVERSATION: cls.HEALTH_EVENTS,
            EventType.MILESTONE: cls.MILESTONES,
            EventType.ALERT: cls.ALERTS
        }
        return mapping.get(event_type, cls.HEALTH_EVENTS)
    
    @classmethod
    def get_all_topics(cls) -> list[str]:
        """Returns all actual topic names"""
        return [
            cls.HEALTH_EVENTS,
            cls.ALERTS,
            cls.BIOMETRIC_UPDATES,
            cls.MILESTONES
        ]
    
    @classmethod
    def get_topic_config(cls, topic_name: str) -> Dict[str, str]:
        """Returns configuration for a given topic"""
        configs = {
            cls.HEALTH_EVENTS: {
                "retention.ms": "2592000000",  # 30 days
                "cleanup.policy": "delete",
                "compression.type": "snappy"
            },
            cls.ALERTS: {
                "retention.ms": "259200000",  # 3 days
                "cleanup.policy": "delete",
                "compression.type": "snappy"
            },
            cls.BIOMETRIC_UPDATES: {
                "retention.ms": "604800000",  # 7 days
                "cleanup.policy": "delete",
                "compression.type": "snappy"
            },
            cls.MILESTONES: {
                "retention.ms": "2592000000",  # 30 days
                "cleanup.policy": "delete",
                "compression.type": "snappy"
            }
        }
        return configs.get(topic_name, {})
