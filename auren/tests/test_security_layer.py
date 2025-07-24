"""
Test Security Layer Implementation
Verifies sanitization, encryption, and role-based filtering
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from cryptography.fernet import Fernet

from auren.realtime.security_layer import (
    SecureEventStreamer, 
    SecurityPolicy,
    EventAccessLevel,
    RoleBasedEventFilter
)
from auren.realtime.crewai_instrumentation import AURENStreamEvent, AURENEventType, AURENPerformanceMetrics


@pytest.fixture
def mock_base_streamer():
    """Create mock base streamer"""
    streamer = AsyncMock()
    streamer.stream_event.return_value = True
    return streamer


@pytest.fixture
def encryption_key():
    """Generate test encryption key"""
    return Fernet.generate_key()


@pytest.fixture
def secure_streamer(mock_base_streamer, encryption_key):
    """Create secure event streamer"""
    return SecureEventStreamer(
        base_streamer=mock_base_streamer,
        encryption_key=encryption_key
    )


@pytest.fixture
def sample_event():
    """Create sample event with sensitive data"""
    return AURENStreamEvent(
        event_id="test_123",
        trace_id="trace_456",
        session_id="session_789",
        timestamp=datetime.now(timezone.utc),
        event_type=AURENEventType.AGENT_EXECUTION_COMPLETED,
        source_agent={"id": "neuroscientist", "role": "neuroscientist"},
        target_agent=None,
        payload={
            "user_id": "user_12345",
            "message": "My HRV is 35 and I'm feeling stressed. Email me at test@example.com",
            "hrv": 35.0,
            "heart_rate": 72,
            "token_cost": 0.025,
            "query": "What should I do about my low HRV?",
            "biometric_data": {
                "sleep_efficiency": 0.78,
                "stress_level": 7.5
            }
        },
        metadata={
            "user_id": "user_12345",
            "session_info": "Contains user_12345 data"
        },
        performance_metrics=AURENPerformanceMetrics(
            latency_ms=1200,
            token_cost=0.025,
            memory_usage_mb=50,
            cpu_percentage=30,
            success=True
        ),
        user_id="user_12345"
    )


class TestSecureEventStreamer:
    
    @pytest.mark.asyncio
    async def test_user_id_sanitization(self, secure_streamer, sample_event, mock_base_streamer):
        """Test that user IDs are properly hashed"""
        
        # Process event
        await secure_streamer.stream_event(sample_event)
        
        # Get the sanitized event
        assert mock_base_streamer.stream_event.called
        sanitized_event = mock_base_streamer.stream_event.call_args[0][0]
        
        # Verify user IDs are hashed
        assert sanitized_event.user_id.startswith("hash_")
        assert sanitized_event.user_id != "user_12345"
        assert len(sanitized_event.user_id) == 17  # "hash_" + 12 chars
        
        # Check payload sanitization
        assert sanitized_event.payload["user_id"].startswith("hash_")
        assert sanitized_event.payload["user_id"] != "user_12345"
        
        # Check metadata sanitization
        assert sanitized_event.metadata["user_id"].startswith("hash_")
        
        # Verify consistent hashing (same input = same hash)
        assert sanitized_event.user_id == sanitized_event.payload["user_id"]
    
    @pytest.mark.asyncio
    async def test_biometric_sanitization(self, secure_streamer, sample_event, mock_base_streamer):
        """Test that biometric values are converted to ranges"""
        
        await secure_streamer.stream_event(sample_event)
        
        sanitized_event = mock_base_streamer.stream_event.call_args[0][0]
        
        # Check HRV sanitization (35 should be in 'normal_low' range)
        assert sanitized_event.payload["hrv"] in ["low", "normal_low", "normal_high", "high"]
        assert isinstance(sanitized_event.payload["hrv"], str)
        
        # Check heart rate sanitization
        assert sanitized_event.payload["heart_rate"] in ["low", "normal_low", "normal_high", "high"]
        
        # Check nested biometric data
        bio_data = sanitized_event.payload["biometric_data"]
        assert bio_data["sleep_efficiency"] in ["low", "normal_low", "normal_high", "high"]
        assert bio_data["stress_level"] in ["low", "normal_low", "normal_high", "high", "above_normal"]
    
    @pytest.mark.asyncio
    async def test_conversation_sanitization(self, secure_streamer, sample_event, mock_base_streamer):
        """Test conversation content sanitization"""
        
        await secure_streamer.stream_event(sample_event)
        
        sanitized_event = mock_base_streamer.stream_event.call_args[0][0]
        
        # Check email removal
        assert "[email]" in sanitized_event.payload["message"]
        assert "test@example.com" not in sanitized_event.payload["message"]
        
        # Check content truncation for long messages
        long_event = sample_event
        long_event.payload["message"] = "x" * 1000
        
        await secure_streamer.stream_event(long_event)
        sanitized_long = mock_base_streamer.stream_event.call_args[0][0]
        
        assert len(sanitized_long.payload["message"]) <= 516  # 500 + "[truncated]"
        assert sanitized_long.payload["message"].endswith("[truncated]")
    
    @pytest.mark.asyncio
    async def test_cost_encryption(self, secure_streamer, sample_event, mock_base_streamer):
        """Test that cost data is encrypted"""
        
        await secure_streamer.stream_event(sample_event)
        
        sanitized_event = mock_base_streamer.stream_event.call_args[0][0]
        
        # Check cost encryption in payload
        assert sanitized_event.payload["token_cost"] != 0.025
        assert sanitized_event.payload["token_cost_encrypted"] is True
        
        # Verify we can decrypt the value
        decrypted = secure_streamer.decrypt_value(sanitized_event.payload["token_cost"])
        assert decrypted == 0.025
        
        # Check performance metrics cost encryption
        assert sanitized_event.performance_metrics.token_cost == 0.0  # Zeroed out
        assert "encrypted_data" in sanitized_event.metadata
        assert "token_cost" in sanitized_event.metadata["encrypted_data"]
    
    @pytest.mark.asyncio
    async def test_query_encryption(self, secure_streamer, sample_event, mock_base_streamer):
        """Test that user queries are encrypted"""
        
        await secure_streamer.stream_event(sample_event)
        
        sanitized_event = mock_base_streamer.stream_event.call_args[0][0]
        
        # Check query encryption
        assert sanitized_event.payload["query"] != "What should I do about my low HRV?"
        assert sanitized_event.payload["query_encrypted"] is True
        
        # Verify decryption
        decrypted = secure_streamer.decrypt_value(sanitized_event.payload["query"])
        assert decrypted == "What should I do about my low HRV?"
    
    @pytest.mark.asyncio
    async def test_security_metadata(self, secure_streamer, sample_event, mock_base_streamer):
        """Test that security metadata is properly added"""
        
        await secure_streamer.stream_event(sample_event)
        
        sanitized_event = mock_base_streamer.stream_event.call_args[0][0]
        
        # Check security metadata
        assert "security" in sanitized_event.metadata
        security_meta = sanitized_event.metadata["security"]
        
        assert security_meta["sanitized"] is True
        assert security_meta["sanitization_version"] == "1.0"
        assert security_meta["access_level"] == EventAccessLevel.ADMIN.value  # Has encrypted data
        assert len(security_meta["sanitized_fields"]) > 0
        assert security_meta["encryption_applied"] is True
        assert "timestamp" in security_meta
    
    @pytest.mark.asyncio
    async def test_statistics_tracking(self, secure_streamer, sample_event):
        """Test that sanitization statistics are tracked"""
        
        # Process multiple events
        for _ in range(5):
            await secure_streamer.stream_event(sample_event)
        
        stats = secure_streamer.get_statistics()
        
        assert stats["total_events"] == 5
        assert stats["sanitized_events"] == 5
        assert stats["encrypted_fields"] > 0
        assert stats["sanitization_rate"] == 1.0
        assert stats["encryption_rate"] > 0


class TestRoleBasedFiltering:
    
    def test_admin_role_access(self):
        """Test admin can see everything"""
        filter = RoleBasedEventFilter()
        
        event = {
            "metadata": {
                "security": {
                    "access_level": EventAccessLevel.ADMIN.value
                }
            },
            "payload": {
                "token_cost": 0.025,
                "user_data": "sensitive"
            }
        }
        
        filtered = filter.filter_event_for_role(event, "admin")
        
        assert filtered is not None
        assert filtered["payload"]["token_cost"] == 0.025  # Not hidden
    
    def test_developer_role_filtering(self):
        """Test developer role filtering"""
        filter = RoleBasedEventFilter()
        
        # Test cost hiding
        event = {
            "metadata": {
                "security": {
                    "access_level": EventAccessLevel.INTERNAL.value
                }
            },
            "payload": {
                "token_cost": 0.025,
                "estimated_cost": 0.10,
                "other_data": "visible"
            }
        }
        
        filtered = filter.filter_event_for_role(event, "developer")
        
        assert filtered is not None
        assert filtered["payload"]["token_cost"] == "[hidden]"
        assert filtered["payload"]["estimated_cost"] == "[hidden]"
        assert filtered["payload"]["other_data"] == "visible"
    
    def test_analyst_access_level_filtering(self):
        """Test analyst can't see privileged events"""
        filter = RoleBasedEventFilter()
        
        # Privileged event
        privileged_event = {
            "metadata": {
                "security": {
                    "access_level": EventAccessLevel.PRIVILEGED.value
                }
            },
            "payload": {}
        }
        
        # Should be filtered out
        filtered = filter.filter_event_for_role(privileged_event, "analyst")
        assert filtered is None
        
        # Public event should be visible
        public_event = {
            "metadata": {
                "security": {
                    "access_level": EventAccessLevel.PUBLIC.value
                }
            },
            "payload": {}
        }
        
        filtered = filter.filter_event_for_role(public_event, "analyst")
        assert filtered is not None
    
    def test_viewer_minimal_access(self):
        """Test viewer only sees public events"""
        filter = RoleBasedEventFilter()
        
        # Test all access levels
        for access_level in EventAccessLevel:
            event = {
                "metadata": {
                    "security": {
                        "access_level": access_level.value
                    }
                },
                "payload": {}
            }
            
            filtered = filter.filter_event_for_role(event, "viewer")
            
            if access_level == EventAccessLevel.PUBLIC:
                assert filtered is not None
            else:
                assert filtered is None


@pytest.mark.integration
class TestSecurityIntegration:
    
    @pytest.mark.asyncio
    async def test_full_security_pipeline(self, secure_streamer, mock_base_streamer):
        """Test complete security pipeline with realistic event"""
        
        # Create event with all sensitive data types
        complex_event = AURENStreamEvent(
            event_id="complex_test",
            trace_id="trace_complex",
            session_id="session_complex",
            timestamp=datetime.now(timezone.utc),
            event_type=AURENEventType.AGENT_COLLABORATION,
            source_agent={"id": "neuroscientist", "role": "neuroscientist", "user_id": "user_999"},
            target_agent={"id": "sleep_specialist", "role": "sleep_specialist"},
            payload={
                "user_id": "user_999",
                "userId": "user_999",  # Alternative format
                "message": "Patient user_999 reports HRV=28, call 555-123-4567 or email patient@example.com",
                "hrv": 28,
                "heart_rate": 85,
                "blood_pressure_systolic": 140,
                "sleep_efficiency": 0.65,
                "stress_level": 8.5,
                "token_cost": 0.045,
                "estimated_cost": 0.15,
                "query": "Analyze my sleep patterns and stress correlation",
                "collaboration_result": {
                    "consensus": True,
                    "confidence": 0.85
                }
            },
            metadata={
                "user_id": "user_999",
                "cost_center": "health_analysis"
            },
            performance_metrics=AURENPerformanceMetrics(
                latency_ms=2500,
                token_cost=0.045,
                memory_usage_mb=75,
                cpu_percentage=45,
                success=True,
                confidence_score=0.85
            ),
            user_id="user_999"
        )
        
        # Process through security
        await secure_streamer.stream_event(complex_event)
        
        # Verify comprehensive sanitization
        sanitized = mock_base_streamer.stream_event.call_args[0][0]
        
        # All user IDs hashed
        assert sanitized.user_id.startswith("hash_")
        assert sanitized.payload["user_id"].startswith("hash_")
        assert sanitized.payload["userId"].startswith("hash_")
        assert sanitized.metadata["user_id"].startswith("hash_")
        assert sanitized.source_agent["user_id"].startswith("hash_")
        
        # Message sanitized
        message = sanitized.payload["message"]
        assert "[email]" in message
        assert "[phone]" in message
        assert "[user_id]" in message
        assert "patient@example.com" not in message
        assert "555-123-4567" not in message
        
        # Biometrics converted to ranges
        assert sanitized.payload["hrv"] in ["low", "below_normal"]
        assert sanitized.payload["heart_rate"] in ["normal_low", "normal_high"]
        assert sanitized.payload["sleep_efficiency"] in ["low", "normal_low"]
        assert sanitized.payload["stress_level"] in ["high", "above_normal"]
        
        # Costs encrypted
        assert sanitized.payload["token_cost_encrypted"] is True
        assert sanitized.payload["estimated_cost_encrypted"] is True
        
        # Query encrypted
        assert sanitized.payload["query_encrypted"] is True
        
        # Security metadata present
        assert sanitized.metadata["security"]["sanitized"] is True
        assert len(sanitized.metadata["security"]["sanitized_fields"]) > 0
        
        # Performance metrics handled
        assert sanitized.performance_metrics.token_cost == 0.0
        assert "encrypted_data" in sanitized.metadata
        
        print(f"✅ Security pipeline test passed - {len(sanitized.metadata['security']['sanitized_fields'])} fields sanitized")


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 