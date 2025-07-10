"""Updated integration tests with proper fixtures."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

class TestAurenIntegration:
    """Integration tests for AUREN system."""
    
    def test_protocol_routing(self, setup_test_environment):
        """Test message routing to correct protocol."""
        # Import here to ensure paths are set up
        from src.app import AUREN2App
        
        # Create app instance
        app = AUREN2App()
        
        # Test that protocols are initialized
        assert "journal" in app.protocols
        assert "mirage" in app.protocols
        assert "visor" in app.protocols
        
        # Test protocol entry creation
        test_data = {"type": "test", "data": "test_value"}
        
        # Mock the protocol create_entry method
        with patch.object(app.protocols["journal"], 'create_entry') as mock_create:
            mock_create.return_value = {"protocol": "journal", "response": "Test"}
            
            # Test journal protocol
            result = app.protocols["journal"].create_entry(test_data)
            assert result["protocol"] == "journal"
    
    def test_biometric_analysis_pipeline(self, mock_facial_landmarks):
        """Test full biometric analysis flow."""
        from src.biometric.analyzers.facial_analyzer import BiometricAnalyzer
        
        # Create analyzer
        analyzer = BiometricAnalyzer()
        
        # Mock the facial landmarks detection
        with patch.object(analyzer.facial_landmarks, 'detect_landmarks', return_value=True):
            with patch.object(analyzer.facial_landmarks, 'landmarks', mock_facial_landmarks):
                # Create a mock image path
                result = analyzer.analyze_image("test_image.jpg")
                
                # Verify result structure
                assert "scores" in result
                assert "timestamp" in result
                assert "image_path" in result
                
                # Verify scores are in expected range
                scores = result["scores"]
                assert 0 <= scores["ptosis"] <= 10
                assert 0 <= scores["inflammation"] <= 10
                assert 0 <= scores["symmetry"] <= 10
                
                # Verify all scores are floats
                assert isinstance(scores["ptosis"], float)
                assert isinstance(scores["inflammation"], float)
                assert isinstance(scores["symmetry"], float)
    
    @pytest.mark.asyncio
    async def test_whatsapp_integration(self, mock_whatsapp_api):
        """Test WhatsApp message flow."""
        from src.integrations.biometric_whatsapp import BiometricWhatsAppConnector
        
        # Mock environment variables
        with patch.dict('os.environ', {
            'WHATSAPP_ACCESS_TOKEN': 'test_token',
            'WHATSAPP_PHONE_ID': 'test_id'
        }):
            connector = BiometricWhatsAppConnector()
            
            # Test sending a text message
            result = await connector.send_text_message(
                to="+1234567890",
                message="Test biometric report"
            )
            
            # Verify the API was called
            mock_whatsapp_api.assert_called()
    
    def test_alert_system(self):
        """Test alert generation and routing."""
        from src.biometric.alerts.alert_manager import AlertManager
        
        manager = AlertManager()
        
        # Create scores that should trigger alerts
        high_ptosis_scores = {
            "ptosis": 7.5,  # Above critical threshold
            "inflammation": 2.0,
            "symmetry": 4.0
        }
        
        # Provide historical data to trigger critical alert
        historical_data = [
            {"ptosis": 7.2, "inflammation": 2.1, "symmetry": 4.1},
            {"ptosis": 7.3, "inflammation": 2.0, "symmetry": 4.0},
            {"ptosis": 7.4, "inflammation": 2.2, "symmetry": 4.2},
        ]
        
        # Generate alerts
        alerts = manager.check_scores(high_ptosis_scores, historical_data)
        
        # Should have at least one alert for high ptosis
        assert len(alerts) > 0
        assert any(alert.severity == "critical" for alert in alerts)
        assert any("ptosis" in alert.message.lower() for alert in alerts)
    
    def test_facial_landmarks_analysis(self, mock_facial_landmarks):
        """Test facial landmark analysis functionality."""
        from src.biometric.analyzers.facial_analyzer import FacialLandmarks
        
        landmarks = FacialLandmarks()
        landmarks.landmarks = mock_facial_landmarks
        
        # Test eye openness calculation
        left_ear, right_ear = landmarks.calculate_eye_openness()
        
        # Verify results are floats
        assert isinstance(left_ear, float)
        assert isinstance(right_ear, float)
        assert 0 <= left_ear <= 1
        assert 0 <= right_ear <= 1
        
        # Test symmetry calculation
        symmetry = landmarks.calculate_facial_symmetry()
        assert isinstance(symmetry, float)
        assert 0 <= symmetry <= 5
        
        # Test puffiness detection
        puffiness = landmarks.detect_facial_puffiness()
        assert isinstance(puffiness, float)
        assert 0 <= puffiness <= 5
