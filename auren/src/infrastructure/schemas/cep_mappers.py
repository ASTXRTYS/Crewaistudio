"""
CEP (Complex Event Processing) event mappers for AUREN Kafka infrastructure.

Provides mapping between Kafka events and CEP-compatible formats for real-time
pattern detection in biometric data.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.infrastructure.schemas.health_events import HealthEvent, TriggerEvent, TriggerType


@dataclass
class CEPEvent:
    """Standardized event format for CEP processing"""
    event_id: str
    timestamp: float
    user_id: str
    event_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]


class CEPEventMapper:
    """
    Maps between Kafka events and CEP-compatible formats for pattern detection.
    
    This class ensures that events flowing through Kafka are in the exact format
    expected by Flink CEP rules for real-time pattern analysis.
    """
    
    @staticmethod
    def map_for_hrv_analysis(event: HealthEvent) -> Optional[CEPEvent]:
        """
        Maps a health event to format expected by HRV CEP rules.
        
        Args:
            event: Health event from Kafka
            
        Returns:
            CEP-compatible event or None if not an HRV event
        """
        if event.data.get("metric_type") != "hrv":
            return None
            
        return CEPEvent(
            event_id=event.event_id,
            timestamp=event.timestamp.timestamp(),
            user_id=event.user_id,
            event_type="hrv_measurement",
            data={
                "hrv_value": float(event.data.get("value", 0)),
                "baseline": float(event.data.get("baseline", 0)),
                "drop_percentage": float(event.data.get("percentage_drop", 0)),
                "measurement_context": event.data.get("measurement_context", "unknown"),
                "device": event.data.get("device", "unknown"),
                "confidence": float(event.data.get("confidence", 0)),
                "quality_score": float(event.data.get("quality_score", 0)),
                "unit": event.data.get("unit", "ms")
            },
            metadata={
                "source": event.source,
                "priority": event.priority.value,
                "original_event_type": event.event_type.value
            }
        )
    
    @staticmethod
    def map_for_sleep_analysis(event: HealthEvent) -> Optional[CEPEvent]:
        """
        Maps events for sleep quality CEP analysis.
        
        Handles sleep-related events and prepares them for pattern detection.
        """
        if event.data.get("metric_type") != "sleep":
            return None
            
        return CEPEvent(
            event_id=event.event_id,
            timestamp=event.timestamp.timestamp(),
            user_id=event.user_id,
            event_type="sleep_measurement",
            data={
                "sleep_duration": float(event.data.get("duration_hours", 0)),
                "sleep_quality": float(event.data.get("quality_score", 0)),
                "deep_sleep_ratio": float(event.data.get("deep_sleep_ratio", 0)),
                "rem_sleep_ratio": float(event.data.get("rem_sleep_ratio", 0)),
                "sleep_efficiency": float(event.data.get("efficiency", 0)),
                "wake_events": int(event.data.get("wake_events", 0)),
                "bedtime": event.data.get("bedtime", ""),
                "waketime": event.data.get("waketime", "")
            },
            metadata={
                "source": event.source,
                "priority": event.priority.value,
                "device": event.data.get("device", "unknown")
            }
        )
    
    @staticmethod
    def map_for_recovery_analysis(event: HealthEvent) -> Optional[CEPEvent]:
        """
        Maps events for recovery pattern CEP analysis.
        
        Focuses on recovery-related metrics like HRV, sleep, and stress indicators.
        """
        metric_type = event.data.get("metric_type")
        
        if metric_type not in ["hrv", "sleep", "stress", "recovery"]:
            return None
            
        base_data = {
            "metric_type": metric_type,
            "value": float(event.data.get("value", 0)),
            "baseline": float(event.data.get("baseline", 0)),
            "deviation": float(event.data.get("deviation", 0)),
            "trend": event.data.get("trend", "stable")
        }
        
        # Add metric-specific data
        if metric_type == "hrv":
            base_data.update({
                "rmssd": float(event.data.get("rmssd", 0)),
                "sdnn": float(event.data.get("sdnn", 0)),
                "pnn50": float(event.data.get("pnn50", 0))
            })
        elif metric_type == "stress":
            base_data.update({
                "cortisol_level": float(event.data.get("cortisol", 0)),
                "stress_score": float(event.data.get("stress_score", 0))
            })
        
        return CEPEvent(
            event_id=event.event_id,
            timestamp=event.timestamp.timestamp(),
            user_id=event.user_id,
            event_type=f"{metric_type}_measurement",
            data=base_data,
            metadata={
                "source": event.source,
                "priority": event.priority.value,
                "context": event.data.get("context", "daily")
            }
        )
    
    @staticmethod
    def create_trigger_from_pattern(
        pattern_data: Dict[str, Any],
        affected_events: List[str],
        trigger_type: TriggerType
    ) -> TriggerEvent:
        """
        Creates a trigger event from CEP pattern detection.
        
        This is what CEP rules will call when patterns are detected in the event stream.
        
        Args:
            pattern_data: Data from pattern detection
            affected_events: List of event IDs that contributed to this trigger
            trigger_type: Type of trigger detected
            
        Returns:
            TriggerEvent ready for Kafka production
        """
        # Determine severity based on pattern type and data
        severity = CEPEventMapper._calculate_severity(pattern_data, trigger_type)
        
        # Determine recommended specialists based on trigger type
        recommended_agents = CEPEventMapper._get_recommended_agents(trigger_type, pattern_data)
        
        # Generate appropriate message
        message = CEPEventMapper._generate_trigger_message(trigger_type, pattern_data)
        
        return TriggerEvent(
            trigger_id=str(uuid.uuid4()),
            user_id=pattern_data.get("user_id", "unknown"),
            trigger_type=trigger_type,
            severity=severity,
            context_window=affected_events,
            recommended_agents=recommended_agents,
            message=message,
            timestamp=datetime.now(),
            metadata={
                "pattern_type": pattern_data.get("pattern_type", "unknown"),
                "confidence": pattern_data.get("confidence", 0.0),
                "window_start": pattern_data.get("window_start"),
                "window_end": pattern_data.get("window_end")
            }
        )
    
    @staticmethod
    def _calculate_severity(pattern_data: Dict[str, Any], trigger_type: TriggerType) -> float:
        """Calculate severity score (0-1) based on pattern data and trigger type"""
        base_severity = 0.5
        
        if trigger_type == TriggerType.HRV_DROP:
            drop_percentage = abs(pattern_data.get("drop_percentage", 0))
            if drop_percentage > 25:
                base_severity = 0.9
            elif drop_percentage > 15:
                base_severity = 0.7
            elif drop_percentage > 10:
                base_severity = 0.5
            else:
                base_severity = 0.3
                
        elif trigger_type == TriggerType.SLEEP_QUALITY_LOW:
            quality_score = pattern_data.get("quality_score", 0)
            if quality_score < 0.3:
                base_severity = 0.9
            elif quality_score < 0.5:
                base_severity = 0.7
            elif quality_score < 0.7:
                base_severity = 0.5
            else:
                base_severity = 0.3
                
        elif trigger_type == TriggerType.RECOVERY_NEEDED:
            recovery_score = pattern_data.get("recovery_score", 0)
            base_severity = max(0.3, 1.0 - recovery_score)
            
        return min(1.0, max(0.0, base_severity))
    
    @staticmethod
    def _get_recommended_agents(trigger_type: TriggerType, pattern_data: Dict[str, Any]) -> list[str]:
        """Determine which specialists should handle this trigger"""
        agent_mapping = {
            TriggerType.HRV_DROP: ["neuroscientist", "coach"],
            TriggerType.SLEEP_QUALITY_LOW: ["neuroscientist", "coach"],
            TriggerType.RECOVERY_NEEDED: ["neuroscientist", "coach", "nutritionist"],
            TriggerType.STRESS_SPIKE: ["neuroscientist", "coach"],
            TriggerType.INFLAMMATION_DETECTED: ["nutritionist", "medical_esthetician"],
            TriggerType.FATIGUE_PATTERN: ["neuroscientist", "coach", "physical_therapy"]
        }
        
        return agent_mapping.get(trigger_type, ["neuroscientist"])
    
    @staticmethod
    def _generate_trigger_message(trigger_type: TriggerType, pattern_data: Dict[str, Any]) -> str:
        """Generate human-readable message for the trigger"""
        message_templates = {
            TriggerType.HRV_DROP: "HRV dropped {drop_percentage:.1f}% below baseline - recovery intervention recommended",
            TriggerType.SLEEP_QUALITY_LOW: "Sleep quality score {quality_score:.1f}/10 indicates poor recovery",
            TriggerType.RECOVERY_NEEDED: "Recovery score {recovery_score:.1f}/10 suggests intervention needed",
            TriggerType.STRESS_SPIKE: "Stress indicators elevated - stress management recommended",
            TriggerType.INFLAMMATION_DETECTED: "Inflammation markers elevated - dietary adjustment suggested",
            TriggerType.FATIGUE_PATTERN: "Fatigue pattern detected - training modification recommended"
        }
        
        template = message_templates.get(trigger_type, "Pattern detected requiring attention")
        
        try:
            return template.format(**pattern_data)
        except KeyError:
            return template


class CEPPatternDetector:
    """
    Helper class for common CEP pattern detection logic.
    
    Provides utilities for detecting patterns that CEP rules will use.
    """
    
    @staticmethod
    def detect_hrv_drop_pattern(events: List[CEPEvent], threshold: float = 15.0) -> Optional[Dict[str, Any]]:
        """
        Detects HRV drop patterns for CEP rules.
        
        Args:
            events: List of HRV events
            threshold: Percentage drop threshold
            
        Returns:
            Pattern data if detected, None otherwise
        """
        if not events:
            return None
            
        hrv_events = [e for e in events if e.event_type == "hrv_measurement"]
        if len(hrv_events) < 2:
            return None
            
        # Sort by timestamp
        hrv_events.sort(key=lambda x: x.timestamp)
        
        # Check for significant drop
        latest = hrv_events[-1]
        baseline = latest.data.get("baseline", 0)
        current = latest.data.get("hrv_value", 0)
        
        if baseline > 0:
            drop_percentage = ((baseline - current) / baseline) * 100
            if drop_percentage >= threshold:
                return {
                    "user_id": latest.user_id,
                    "drop_percentage": drop_percentage,
                    "current_value": current,
                    "baseline": baseline,
                    "pattern_type": "hrv_drop",
                    "confidence": 0.85,
                    "window_start": hrv_events[0].timestamp,
                    "window_end": latest.timestamp
                }
                
        return None
    
    @staticmethod
    def detect_sleep_quality_pattern(events: List[CEPEvent], threshold: float = 0.5) -> Optional[Dict[str, Any]]:
        """
        Detects sleep quality patterns for CEP rules.
        
        Args:
            events: List of sleep events
            threshold: Quality score threshold
            
        Returns:
            Pattern data if detected, None otherwise
        """
        sleep_events = [e for e in events if e.event_type == "sleep_measurement"]
        if not sleep_events:
            return None
            
        # Use latest sleep event
        latest = max(sleep_events, key=lambda x: x.timestamp)
        quality_score = latest.data.get("sleep_quality", 0)
        
        if quality_score < threshold:
            return {
                "user_id": latest.user_id,
                "quality_score": quality_score,
                "pattern_type": "sleep_quality_low",
                "confidence": 0.9,
                "window_start": latest.timestamp - 86400,  # 24 hours
                "window_end": latest.timestamp
            }
            
        return None


# Convenience functions for common operations
def map_event_for_cep(event: HealthEvent, analysis_type: str) -> Optional[CEPEvent]:
    """
    Convenience function to map events based on analysis type.
    
    Args:
        event: Health event
        analysis_type: Type of analysis ('hrv', 'sleep', 'recovery')
        
    Returns:
        CEP-compatible event or None
    """
    mappers = {
        "hrv": CEPEventMapper.map_for_hrv_analysis,
        "sleep": CEPEventMapper.map_for_sleep_analysis,
        "recovery": CEPEventMapper.map_for_recovery_analysis
    }
    
    mapper = mappers.get(analysis_type)
    if mapper:
        return mapper(event)
    return None
