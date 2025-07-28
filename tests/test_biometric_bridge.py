"""
Tests for AUREN Biometric Bridge
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
import json

from auren.biometric.types import (
    BiometricReading, BiometricEvent, WearableType, 
    CognitiveMode, NEUROSState
)
from auren.biometric.handlers import AppleHealthKitHandler
from auren.biometric.bridge import BiometricKafkaLangGraphBridge, load_biometric_config


@pytest.fixture
def mock_kafka_producer():
    """Mock Kafka producer for testing"""
    producer = Mock()
    producer.send = Mock(return_value=Mock())
    producer.flush = Mock()
    producer.close = Mock()
    return producer


@pytest.fixture
def mock_postgres_pool():
    """Mock PostgreSQL connection pool"""
    pool = AsyncMock()
    pool.acquire = AsyncMock()
    return pool


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = Mock()
    client.set = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.hset = AsyncMock(return_value=1)
    client.expire = AsyncMock(return_value=True)
    client.pipeline = Mock(return_value=Mock(
        hset=Mock(return_value=Mock()),
        expire=Mock(return_value=Mock()),
        execute=Mock(return_value=[])
    ))
    client.ping = Mock(return_value=True)
    return client


@pytest.fixture
def mock_graph():
    """Mock LangGraph compiled graph"""
    graph = AsyncMock()
    graph.ainvoke = AsyncMock(return_value={"messages": [], "current_mode": CognitiveMode.PATTERN})
    return graph


class TestBiometricTypes:
    """Test biometric data types"""
    
    def test_biometric_reading_validation(self):
        """Test BiometricReading validation"""
        # Valid reading
        reading = BiometricReading(
            metric="heart_rate",
            value=72.0,
            timestamp=datetime.now(timezone.utc),
            confidence=0.95
        )
        assert reading.metric == "heart_rate"
        assert reading.value == 72.0
        assert reading.confidence == 0.95
        
        # Invalid confidence
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            BiometricReading(
                metric="heart_rate",
                value=72.0,
                timestamp=datetime.now(timezone.utc),
                confidence=1.5
            )
        
        # Invalid negative value
        with pytest.raises(ValueError, match="Biometric value cannot be negative"):
            BiometricReading(
                metric="heart_rate",
                value=-10.0,
                timestamp=datetime.now(timezone.utc)
            )
    
    def test_biometric_event_serialization(self):
        """Test BiometricEvent serialization"""
        timestamp = datetime.now(timezone.utc)
        reading = BiometricReading(
            metric="hrv",
            value=55.0,
            timestamp=timestamp,
            confidence=0.9
        )
        
        event = BiometricEvent(
            device_type=WearableType.OURA,
            user_id="test_user_123",
            timestamp=timestamp,
            readings=[reading]
        )
        
        # Test to_dict
        event_dict = event.to_dict()
        assert event_dict["device_type"] == "oura"
        assert event_dict["user_id"] == "test_user_123"
        assert len(event_dict["readings"]) == 1
        assert event_dict["readings"][0]["metric"] == "hrv"
        assert event_dict["readings"][0]["value"] == 55.0


class TestAppleHealthKitHandler:
    """Test Apple HealthKit handler"""
    
    @pytest.mark.asyncio
    async def test_healthkit_single_push(self, mock_kafka_producer):
        """Test processing single HealthKit push"""
        handler = AppleHealthKitHandler(mock_kafka_producer)
        
        data = {
            "user_id": "test_user",
            "samples": [
                {
                    "type": "heartRate",
                    "value": 72,
                    "timestamp": "2025-01-27T10:30:00Z",
                    "unit": "bpm",
                    "source": "Apple Watch"
                }
            ]
        }
        
        event = await handler.handle_healthkit_push(data)
        
        assert event is not None
        assert event.device_type == WearableType.APPLE_HEALTH
        assert event.user_id == "test_user"
        assert len(event.readings) == 1
        assert event.readings[0].metric == "heart_rate"
        assert event.readings[0].value == 72.0
        assert event.readings[0].confidence == 1.0  # Apple Watch = high confidence
    
    @pytest.mark.asyncio
    async def test_healthkit_batch_processing(self, mock_kafka_producer):
        """Test batch processing of HealthKit data"""
        handler = AppleHealthKitHandler(mock_kafka_producer)
        
        batch_data = [
            {
                "user_id": f"user_{i}",
                "samples": [
                    {
                        "type": "heartRate",
                        "value": 70 + i,
                        "timestamp": f"2025-01-27T10:{i:02d}:00Z",
                        "unit": "bpm",
                        "source": "Apple Watch"
                    }
                ]
            }
            for i in range(5)
        ]
        
        events = await handler.handle_healthkit_batch(batch_data)
        
        assert len(events) == 5
        for i, event in enumerate(events):
            assert event.user_id == f"user_{i}"
            assert event.readings[0].value == 70 + i
    
    def test_temperature_conversion(self, mock_kafka_producer):
        """Test Fahrenheit to Celsius conversion"""
        handler = AppleHealthKitHandler(mock_kafka_producer)
        
        # Fahrenheit value
        celsius = handler._convert_temperature_if_needed(98.6)
        assert 36.9 < celsius < 37.1  # ~37°C
        
        # Already Celsius
        celsius = handler._convert_temperature_if_needed(37.0)
        assert celsius == 37.0
    
    def test_value_validation(self, mock_kafka_producer):
        """Test biometric value range validation"""
        handler = AppleHealthKitHandler(mock_kafka_producer)
        
        # Valid heart rate
        assert handler._validate_value_range("heart_rate", 72) is True
        
        # Invalid heart rate
        assert handler._validate_value_range("heart_rate", 300) is False
        assert handler._validate_value_range("heart_rate", -10) is False
        
        # Valid HRV
        assert handler._validate_value_range("hrv", 55) is True
        
        # Invalid HRV
        assert handler._validate_value_range("hrv", 400) is False


class TestBiometricKafkaLangGraphBridge:
    """Test Kafka-LangGraph bridge"""
    
    def test_config_loading(self):
        """Test configuration loading with defaults"""
        config = load_biometric_config("nonexistent.yaml")
        
        assert config["thresholds"]["hrv_drop_ms"] == 25
        assert config["thresholds"]["heart_rate_elevated"] == 100
        assert config["baselines"]["hrv_default"] == 60
    
    @pytest.mark.asyncio
    async def test_create_initial_state(self, mock_graph, mock_postgres_pool, 
                                       mock_redis_client, mock_kafka_producer):
        """Test initial state creation"""
        kafka_config = {"bootstrap_servers": "localhost:9092"}
        bridge = BiometricKafkaLangGraphBridge(
            mock_graph, kafka_config, mock_postgres_pool, 
            mock_redis_client, max_concurrent_events=10
        )
        
        state = bridge._create_initial_state("user_123", "session_456")
        
        assert state["user_id"] == "user_123"
        assert state["session_id"] == "session_456"
        assert state["current_mode"] == CognitiveMode.PATTERN
        assert state["mode_confidence"] == 0.5
        assert state["checkpoint_version"] == 1
    
    def test_stress_level_calculation(self, mock_graph, mock_postgres_pool,
                                    mock_redis_client, mock_kafka_producer):
        """Test stress level calculation from biometrics"""
        kafka_config = {"bootstrap_servers": "localhost:9092"}
        bridge = BiometricKafkaLangGraphBridge(
            mock_graph, kafka_config, mock_postgres_pool, 
            mock_redis_client
        )
        
        # High stress scenario
        analysis = {
            "metrics": {
                "hrv": {
                    "current": 35,
                    "baseline": 60,
                    "drop": 25,
                    "drop_percentage": 41.67,
                    "significant": True
                },
                "heart_rate": {
                    "current": 95,
                    "elevation": 25,
                    "elevated": False
                }
            }
        }
        
        stress = bridge._calculate_stress_level(analysis)
        assert stress > 0.5  # Should indicate high stress
    
    def test_reflex_trigger_detection(self, mock_graph, mock_postgres_pool,
                                    mock_redis_client, mock_kafka_producer):
        """Test reflex mode trigger detection"""
        kafka_config = {"bootstrap_servers": "localhost:9092"}
        bridge = BiometricKafkaLangGraphBridge(
            mock_graph, kafka_config, mock_postgres_pool, 
            mock_redis_client
        )
        
        # Scenario that should trigger reflex mode
        metrics = {
            "hrv": {
                "drop": 30,  # > 25ms threshold
                "drop_percentage": 50  # > 30% threshold
            }
        }
        
        triggered, reason = bridge._check_reflex_triggers(metrics, [])
        assert triggered is True
        assert "HRV dropped" in reason
    
    def test_mode_confidence_calculation(self, mock_graph, mock_postgres_pool,
                                       mock_redis_client, mock_kafka_producer):
        """Test confidence calculation for mode switches"""
        kafka_config = {"bootstrap_servers": "localhost:9092"}
        bridge = BiometricKafkaLangGraphBridge(
            mock_graph, kafka_config, mock_postgres_pool, 
            mock_redis_client
        )
        
        # Test reflex confidence
        metrics = {
            "hrv": {"significant": True, "drop": 35},
            "heart_rate": {"elevated": True, "current": 110}
        }
        
        confidence = bridge._calculate_reflex_confidence(metrics)
        assert 0.5 <= confidence <= 1.0
        
        # Test guardian confidence
        metrics = {"recovery": {"current": 30}}  # Low recovery
        confidence = bridge._calculate_guardian_confidence(metrics)
        assert confidence > 0.5


class TestMockBiometricEventGenerator:
    """Test utilities for generating mock biometric events"""
    
    def generate_mock_event(self, user_id: str, hrv: float = 60, 
                          heart_rate: float = 70, stress: float = 0.3) -> dict:
        """Generate a mock biometric event for testing"""
        timestamp = datetime.now(timezone.utc)
        
        return {
            "device_type": "oura",
            "user_id": user_id,
            "timestamp": timestamp.isoformat(),
            "readings": [
                {
                    "metric": "hrv",
                    "value": hrv,
                    "timestamp": timestamp.isoformat(),
                    "confidence": 0.95
                },
                {
                    "metric": "heart_rate",
                    "value": heart_rate,
                    "timestamp": timestamp.isoformat(),
                    "confidence": 0.95
                },
                {
                    "metric": "stress_level",
                    "value": stress,
                    "timestamp": timestamp.isoformat(),
                    "confidence": 0.8
                }
            ]
        }
    
    def test_mock_event_generation(self):
        """Test mock event generation"""
        event_data = self.generate_mock_event("test_user", hrv=45, heart_rate=95)
        
        # Should be valid for BiometricEvent creation
        event = BiometricEvent(
            device_type=WearableType(event_data["device_type"]),
            user_id=event_data["user_id"],
            timestamp=datetime.fromisoformat(event_data["timestamp"]),
            readings=[
                BiometricReading(
                    metric=r["metric"],
                    value=r["value"],
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    confidence=r["confidence"]
                )
                for r in event_data["readings"]
            ]
        )
        
        assert event.user_id == "test_user"
        assert len(event.readings) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 