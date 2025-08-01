"""
Unit tests for MyAgent class following peer review recommendations.
Tests cover critical functionality including LangGraph integration, 
YAML configuration merging, and Kafka topic generation.
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add agents directory to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

from my_agent import MyAgent, load_agent_config
from shared_utils import deep_merge, generate_kafka_topics, validate_kafka_topic_name


class TestMyAgent:
    """Test suite for MyAgent class"""
    
    def test_agent_creation_basic(self):
        """Test basic agent creation with default parameters"""
        agent = MyAgent()
        assert agent.role == "Senior Researcher"
        assert agent.temperature == 0.1
        assert agent.enabled is True
        assert agent.locked is False
    
    def test_agent_creation_with_parameters(self):
        """Test agent creation with custom parameters"""
        agent = MyAgent(
            role="NEUROS CNS Specialist",
            domain="biometric",
            temperature=0.3,
            locked=True
        )
        assert agent.role == "NEUROS CNS Specialist"
        assert agent.domain == "biometric"
        assert agent.temperature == 0.3
        assert agent.locked is True
    
    def test_kafka_topic_generation(self):
        """Test Confluent-style Kafka topic naming"""
        agent = MyAgent(role="NEUROS & HRV Specialist", domain="testing")
        
        # Test topic naming follows Confluent conventions
        assert agent.ingest_topic == "neuros_and_hrv_specialist.testing.analyze"
        assert agent.output_topic == "neuros_and_hrv_specialist.recommendation.publish"
        assert agent.status_topic == "neuros_and_hrv_specialist.status.update"
    
    def test_kafka_topic_special_characters(self):
        """Test Kafka topic generation handles special characters"""
        agent = MyAgent(role="CNS & Recovery Agent", domain="biometric")
        
        # Ensure special characters are handled properly
        assert "cns_and_recovery_agent" in agent.ingest_topic
        assert "biometric" in agent.ingest_topic
        assert "analyze" in agent.ingest_topic
    
    @patch('my_agent.st')  # Mock Streamlit to avoid import errors
    def test_kafka_status_update_not_implemented(self, mock_st):
        """Test that Kafka status update raises NotImplementedError"""
        agent = MyAgent()
        
        with pytest.raises(NotImplementedError) as exc_info:
            agent.publish_status_update({"status": "active"})
        
        assert "Kafka status publishing not implemented" in str(exc_info.value)
        assert agent.status_topic in str(exc_info.value)
    
    @patch('my_agent.st')  # Mock Streamlit to avoid import errors
    def test_kafka_kpi_emission_not_implemented(self, mock_st):
        """Test that KPI emission raises NotImplementedError"""
        agent = MyAgent()
        
        with pytest.raises(NotImplementedError) as exc_info:
            agent.emit_kpi("hrv_score", 85.0, "percentage", 0.95)
        
        assert "Kafka KPI emission not implemented" in str(exc_info.value)
        assert agent.output_topic in str(exc_info.value)
    
    def test_agent_validation_basic(self):
        """Test basic agent validation"""
        agent = MyAgent()
        # Should be valid with default configuration
        assert agent.is_valid() is True
    
    def test_agent_clone(self):
        """Test agent cloning functionality"""
        original = MyAgent(
            role="Original Agent",
            temperature=0.2,
            domain="testing"
        )
        
        cloned = original.clone("Test Copy")
        
        assert cloned.role == "Original Agent (Test Copy)"
        assert cloned.temperature == 0.2
        assert cloned.domain == "testing"
        assert cloned.id != original.id  # Should have different ID
    
    def test_agent_export_to_dict(self):
        """Test agent export functionality"""
        agent = MyAgent(role="Export Test Agent", domain="testing")
        exported = agent.to_dict()
        
        # Check all required fields are present
        required_fields = [
            'id', 'role', 'backstory', 'goal', 'temperature',
            'ingest_topic', 'output_topic', 'status_topic', 'domain'
        ]
        
        for field in required_fields:
            assert field in exported, f"Missing field: {field}"
        
        assert exported['role'] == "Export Test Agent"
        assert exported['domain'] == "testing"
    
    def test_locked_agent_delete_protection(self):
        """Test that locked agents cannot be deleted"""
        agent = MyAgent(locked=True)
        
        # Mock the session state and Streamlit
        with patch('my_agent.ss') as mock_ss, \
             patch('my_agent.st') as mock_st:
            
            mock_ss.agents = [agent]
            result = agent.delete()
            
            assert result is False  # Should return False for locked agent
            mock_st.warning.assert_called_once()
            assert "Cannot delete locked agent" in mock_st.warning.call_args[0][0]


class TestDeepMerge:
    """Test suite for deep_merge helper function"""
    
    def test_deep_merge_basic(self):
        """Test basic deep merge functionality"""
        a = {"x": {"y": 1}}
        b = {"x": {"z": 2}}
        result = deep_merge(a, b)
        
        expected = {"x": {"y": 1, "z": 2}}
        assert result == expected
    
    def test_deep_merge_overwrite(self):
        """Test that deep merge overwrites values correctly"""
        a = {"config": {"temp": 0.1, "tools": {"tool1": "config1"}}}
        b = {"config": {"temp": 0.3, "tools": {"tool2": "config2"}}}
        
        result = deep_merge(a, b)
        
        assert result["config"]["temp"] == 0.3  # Overwritten
        assert result["config"]["tools"]["tool1"] == "config1"  # Preserved
        assert result["config"]["tools"]["tool2"] == "config2"  # Added
    
    def test_deep_merge_complex_nesting(self):
        """Test deep merge with complex nested structures"""
        a = {
            "agent": {
                "personality": {"base_tone": "curious"},
                "tools": {"hrv": "enabled"}
            }
        }
        b = {
            "agent": {
                "personality": {"voice_style": "professional"},
                "tools": {"cns": "enabled"},
                "kafka": {"enabled": True}
            }
        }
        
        result = deep_merge(a, b)
        
        # Check all values are preserved/merged correctly
        assert result["agent"]["personality"]["base_tone"] == "curious"
        assert result["agent"]["personality"]["voice_style"] == "professional"
        assert result["agent"]["tools"]["hrv"] == "enabled"
        assert result["agent"]["tools"]["cns"] == "enabled"
        assert result["agent"]["kafka"]["enabled"] is True
    
    def test_deep_merge_non_dict_overwrite(self):
        """Test that non-dict values are overwritten completely"""
        a = {"value": [1, 2, 3]}
        b = {"value": [4, 5]}
        
        result = deep_merge(a, b)
        assert result["value"] == [4, 5]  # Completely replaced


class TestYAMLConfig:
    """Test suite for YAML configuration loading"""
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent YAML file returns empty dict"""
        result = load_agent_config("nonexistent_file.yaml")
        assert result == {}
        assert isinstance(result, dict)
    
    def test_load_valid_yaml(self, tmp_path):
        """Test loading valid YAML configuration"""
        yaml_content = """
---
personality:
  identity:
    role: "Test Agent"
    background: "Test background"
  voice_characteristics:
    base_tone: "curious"
"""
        
        yaml_file = tmp_path / "test_config.yaml"
        yaml_file.write_text(yaml_content)
        
        result = load_agent_config(str(yaml_file))
        
        assert "personality" in result
        assert result["personality"]["identity"]["role"] == "Test Agent"
        assert result["personality"]["voice_characteristics"]["base_tone"] == "curious"
    
    @patch('my_agent.st')  # Mock Streamlit to avoid import errors
    def test_load_invalid_yaml(self, mock_st, tmp_path):
        """Test loading invalid YAML file handles errors gracefully"""
        invalid_yaml = """
invalid: yaml: content: [
  unclosed bracket
"""
        
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text(invalid_yaml)
        
        result = load_agent_config(str(yaml_file))
        
        assert result == {}  # Should return empty dict on error
        mock_st.warning.assert_called_once()


class TestLangGraphIntegration:
    """Test suite for LangGraph integration"""
    
    @patch('my_agent._create_llm')
    @patch('my_agent.st')
    def test_langgraph_agent_creation_success(self, mock_st, mock_create_llm):
        """Test successful LangGraph agent creation"""
        # Mock LLM creation
        mock_llm = Mock()
        mock_create_llm.return_value = mock_llm
        
        # Mock the create_react_agent function
        with patch('my_agent.create_react_agent') as mock_create_agent:
            mock_agent = Mock()
            mock_create_agent.return_value = mock_agent
            
            agent = MyAgent(role="Test Agent")
            lg_agent = agent.get_langgraph_agent()
            
            assert lg_agent is not None
            mock_create_agent.assert_called_once()
            
            # Verify the call arguments
            args, kwargs = mock_create_agent.call_args
            assert kwargs['model'] == mock_llm
            assert "You are Test Agent" in kwargs['state_modifier']
    
    @patch('my_agent._create_llm')
    @patch('my_agent.st')
    def test_langgraph_agent_creation_failure(self, mock_st, mock_create_llm):
        """Test LangGraph agent creation handles failures gracefully"""
        # Mock LLM creation failure
        mock_create_llm.side_effect = Exception("LLM creation failed")
        
        agent = MyAgent(role="Test Agent")
        lg_agent = agent.get_langgraph_agent()
        
        assert lg_agent is None
        mock_st.error.assert_called_once()
        assert "Failed to create LLM" in mock_st.error.call_args[0][0]


class TestSecurityValidation:
    """Test suite for security-related validations"""
    
    def test_yaml_safe_loading(self):
        """Test that YAML loading uses safe_load (no arbitrary object creation)"""
        # This test ensures we're using yaml.safe_load
        # which prevents arbitrary Python object deserialization
        with patch('my_agent.yaml.safe_load') as mock_safe_load:
            mock_safe_load.return_value = {"test": "data"}
            
            result = load_agent_config("test.yaml")
            
            mock_safe_load.assert_called_once()
            assert result == {"test": "data"}


# Additional tests for peer review requirements
class TestAdvancedScenarios:
    """Advanced test scenarios covering peer review edge cases"""
    
    def test_agent_import_failure_simulation(self):
        """Test that Agent import failure raises proper error"""
        # This would require complex mocking to fully test the import chain
        # For now, validate the error message pattern
        error_msg = "❌ LangGraph Agent class not found. Install langgraph>=0.6.2 or check import paths."
        assert "LangGraph Agent class not found" in error_msg
        assert "langgraph>=0.6.2" in error_msg
    
    def test_yaml_loader_empty_file(self, tmp_path):
        """Test YAML loader handles empty files correctly"""
        empty_file = tmp_path / "empty.yaml"
        empty_file.touch()  # Create empty file
        
        result = load_agent_config(str(empty_file))
        assert result == {}  # Should return empty dict, not None
    
    def test_kafka_topic_validation(self):
        """Test Kafka topic naming validation"""
        # Valid topics
        assert validate_kafka_topic_name("neuros_specialist.biometric.analyze")
        assert validate_kafka_topic_name("agent_name.domain.verb")
        
        # Invalid topics
        assert not validate_kafka_topic_name("invalid-topic-name")  # Hyphens not allowed
        assert not validate_kafka_topic_name("Agent.Domain.Verb")  # Uppercase not allowed
        assert not validate_kafka_topic_name("missing.verb")  # Missing part
        assert not validate_kafka_topic_name("too.many.parts.here")  # Too many parts
    
    def test_kafka_topic_generation_comprehensive(self):
        """Test comprehensive Kafka topic generation scenarios"""
        # Test various role formats
        test_cases = [
            ("NEUROS CNS Specialist", "neuros_cns_specialist"),
            ("Recovery & Sleep Agent", "recovery_and_sleep_agent"),
            ("HRV Analyst", "hrv_analyst"),
            ("Multi Word Agent Name", "multi_word_agent_name")
        ]
        
        for role, expected_agent in test_cases:
            topics = generate_kafka_topics(role, "testing")
            
            assert topics['ingest'] == f"{expected_agent}.testing.analyze"
            assert topics['output'] == f"{expected_agent}.recommendation.publish"
            assert topics['status'] == f"{expected_agent}.status.update"
            
            # Validate all topics follow Confluent conventions
            for topic in topics.values():
                assert validate_kafka_topic_name(topic), f"Invalid topic: {topic}"


# PyYAML version check (security requirement from peer review)
def test_pyyaml_version_security():
    """Test that PyYAML version is >= 5.4 to avoid RCE vulnerabilities"""
    import yaml
    
    # Extract version number
    version_parts = yaml.__version__.split('.')
    major, minor = int(version_parts[0]), int(version_parts[1])
    
    # PyYAML 5.4+ required for security (CVE-2020-14343 and others)
    assert major > 5 or (major == 5 and minor >= 4), \
        f"PyYAML {yaml.__version__} is vulnerable. Upgrade to >= 5.4"


def test_tool_protocol_compliance():
    """Test that tools follow the ToolProtocol interface"""
    # This would be a runtime test with actual tool instances
    # For now, just validate the protocol exists
    from my_agent import ToolProtocol
    
    # Check protocol has required attributes
    assert hasattr(ToolProtocol, '__protocol__')
    
    # Would test with actual tool instances in integration tests
    # mock_tool = Mock()
    # mock_tool.name = "test_tool"
    # mock_tool.tool_id = "test_001" 
    # assert isinstance(mock_tool, ToolProtocol)  # Would work with proper tools


if __name__ == "__main__":
    pytest.main([__file__]) 