"""Unit tests for biometric data models"""

import pytest
from datetime import datetime
from auren.biometric.bridge import (
    BiometricReading,
    BiometricEvent,
    WearableType,
    ValidationError
)


class TestBiometricReading:
    """Test BiometricReading data model"""
    
    def test_valid_reading_creation(self):
        """Test creating a valid biometric reading"""
        reading = BiometricReading(
            metric="hrv",
            value=65.0,
            timestamp=datetime.now(),
            confidence=0.95
        )
        assert reading.metric == "hrv"
        assert reading.value == 65.0
        assert reading.confidence == 0.95
    
    def test_invalid_confidence_range(self):
        """Test that confidence must be between 0 and 1"""
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            BiometricReading(
                metric="hrv",
                value=65.0,
                timestamp=datetime.now(),
                confidence=1.5
            )
    
    def test_negative_value_validation(self):
        """Test that most biometric values cannot be negative"""
        with pytest.raises(ValueError, match="Biometric value cannot be negative"):
            BiometricReading(
                metric="heart_rate",
                value=-10.0,
                timestamp=datetime.now()
            )
    
    def test_temperature_deviation_can_be_negative(self):
        """Test that temperature deviation is allowed to be negative"""
        reading = BiometricReading(
            metric="temperature_deviation",
            value=-0.5,
            timestamp=datetime.now()
        )
        assert reading.value == -0.5


class TestBiometricEvent:
    """Test BiometricEvent data model"""
    
    def test_event_creation(self):
        """Test creating a biometric event"""
        timestamp = datetime.now()
        event = BiometricEvent(
            device_type=WearableType.OURA_RING,
            user_id="test_user_123",
            timestamp=timestamp,
            readings=[]
        )
        assert event.device_type == WearableType.OURA_RING
        assert event.user_id == "test_user_123"
        assert event.timestamp == timestamp
    
    def test_event_properties(self):
        """Test biometric event property accessors"""
        event = BiometricEvent(
            device_type=WearableType.WHOOP_BAND,
            user_id="test_user",
            timestamp=datetime.now(),
            readings=[
                BiometricReading(metric="hrv", value=55.0, timestamp=datetime.now()),
                BiometricReading(metric="heart_rate", value=72.0, timestamp=datetime.now()),
                BiometricReading(metric="stress_level", value=0.3, timestamp=datetime.now())
            ]
        )
        
        assert event.hrv == 55.0
        assert event.heart_rate == 72
        assert event.stress_level == 0.3
    
    def test_event_serialization(self):
        """Test event serialization to dict"""
        timestamp = datetime.now()
        event = BiometricEvent(
            device_type=WearableType.APPLE_HEALTH,
            user_id="test_user",
            timestamp=timestamp,
            readings=[
                BiometricReading(metric="steps", value=10000, timestamp=timestamp)
            ]
        )
        
        data = event.to_dict()
        assert data["device_type"] == "apple_health"
        assert data["user_id"] == "test_user"
        assert len(data["readings"]) == 1
        assert data["readings"][0]["metric"] == "steps"
        assert data["readings"][0]["value"] == 10000
    
    def test_event_deserialization(self):
        """Test event deserialization from dict"""
        timestamp = datetime.now()
        data = {
            "device_type": "oura_ring",
            "user_id": "test_user",
            "timestamp": timestamp.isoformat(),
            "readings": [
                {
                    "metric": "sleep_score",
                    "value": 85.0,
                    "timestamp": timestamp.isoformat(),
                    "confidence": 0.9
                }
            ]
        }
        
        event = BiometricEvent.from_dict(data)
        assert event.device_type == WearableType.OURA_RING
        assert event.user_id == "test_user"
        assert len(event.readings) == 1
        assert event.readings[0].metric == "sleep_score"
        assert event.readings[0].value == 85.0 