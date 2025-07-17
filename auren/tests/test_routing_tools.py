"""
Comprehensive unit tests for AUREN routing tools.

These tests ensure the routing system correctly identifies specialists,
handles edge cases, and maintains data integrity.
"""

import json
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import routing tools
import sys
sys.path.append('src')
from tools.routing_tools import (
    RoutingLogicTool,
    DirectRoutingTool,
    SpecialistRegistry,
    PacketBuilder,
    SpecialistDomain,
    RoutingDecision
)


class TestRoutingLogicTool:
    """Test the intelligent message routing system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = RoutingLogicTool()
    
    def test_neuroscience_routing(self):
        """Test routing to neuroscience specialist."""
        message = "I've been having trouble sleeping and feel cognitively foggy"
        result = self.tool._run(message)
        decision = json.loads(result)
        
        assert decision['primary_specialist'] == 'neuroscience'
        assert decision['confidence'] > 0.5
        assert 'sleep' in decision['reasoning'].lower()
    
    def test_nutrition_routing(self):
        """Test routing to nutrition specialist."""
        message = "What should I eat before my workout?"
        result = self.tool._run(message)
        decision = json.loads(result)
        
        assert decision['primary_specialist'] == 'nutrition'
        assert decision['confidence'] > 0.5
    
    def test_fitness_routing(self):
        """Test routing to fitness specialist."""
        message = "My workout routine needs adjustment"
        result = self.tool._run(message)
        decision = json.loads(result)
        
        assert decision['primary_specialist'] == 'fitness'
        assert decision['confidence'] > 0.5
    
    def test_physical_therapy_routing(self):
        """Test routing to physical therapy specialist."""
        message = "My knee hurts during squats"
        result = self.tool._run(message)
        decision = json.loads(result)
        
        assert decision['primary_specialist'] == 'physical_therapy'
        assert decision['confidence'] > 0.5
    
    def test_medical_esthetics_routing(self):
        """Test routing to medical esthetics specialist."""
        message = "How can I improve my skin's appearance?"
        result = self.tool._run(message)
        decision = json.loads(result)
        
        assert decision['primary_specialist'] == 'medical_esthetics'
        assert decision['confidence'] > 0.5
    
    def test_general_fallback(self):
        """Test fallback to general specialist."""
        message = "Hello, how are you?"
        result = self.tool._run(message)
        decision = json.loads(result)
        
        assert decision['primary_specialist'] == 'general'
        assert decision['confidence'] < 0.6
    
    def test_collaboration_detection(self):
        """Test detection of multi-specialist needs."""
        message = "I have knee pain and need nutrition advice for recovery"
        result = self.tool._run(message)
        decision = json.loads(result)
        
        assert decision['requires_collaboration'] == True
        assert len(decision['secondary_specialists']) > 0
    
    def test_urgency_detection(self):
        """Test urgency level detection."""
        urgent_message = "This is urgent - I can't sleep at all"
        result = self.tool._run(urgent_message)
        decision = json.loads(result)
        
        assert decision['urgency_level'] in ['high', 'critical']
    
    def test_normal_urgency(self):
        """Test normal urgency for standard messages."""
        message = "I have a question about my diet"
        result = self.tool._run(message)
        decision = json.loads(result)
        
        assert decision['urgency_level'] == 'normal'


class TestDirectRoutingTool:
    """Test explicit specialist request handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = DirectRoutingTool()
    
    def test_nutritionist_direct_request(self):
        """Test direct request to nutritionist."""
        message = "I want to talk to my nutritionist about my macros"
        result = self.tool._run(message)
        decision = json.loads(result)
        
        assert decision['primary_specialist'] == 'nutrition'
        assert decision['confidence'] > 0.9
    
    def test_neuroscientist_direct_request(self):
        """Test direct request to neuroscientist."""
        message = "Ask my neuroscientist about sleep optimization"
        result = self.tool._run(message)
        decision = json.loads(result)
        
        assert decision['primary_specialist'] == 'neuroscience'
        assert decision['confidence'] > 0.9
    
    def test_trainer_direct_request(self):
        """Test direct request to trainer."""
        message = "Connect me with my trainer for workout advice"
        result = self.tool._run(message)
        decision = json.loads(result)
        
        assert decision['primary_specialist'] == 'fitness'
        assert decision['confidence'] > 0.9
    
    def test_no_direct_request(self):
        """Test when no direct request is made."""
        message = "I have a general question"
        result = self.tool._run(message)
        
        assert result == '{"status": "no_direct_request"}'
    
    def test_various_phrasings(self):
        """Test different ways of requesting specialists."""
        phrasings = [
            "talk to my nutritionist",
            "ask my trainer",
            "what does my neuroscientist think",
            "connect me with my physical therapist",
            "consult my esthetician"
        ]
        
        for phrase in phrasings:
            result = self.tool._run(phrase)
            decision = json.loads(result)
            assert 'primary_specialist' in decision


class TestSpecialistRegistry:
    """Test specialist registration and management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry_path = Path(self.temp_dir) / "test_registry.json"
        self.registry = SpecialistRegistry(self.registry_path)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.registry_path.exists():
            self.registry_path.unlink()
        os.rmdir(self.temp_dir)
    
    def test_initial_load(self):
        """Test loading initial registry."""
        # Should load default specialists
        available = self.registry.get_available_specialists()
        assert len(available) > 0
    
    def test_specialist_query(self):
        """Test querying specialist by domain."""
        result = self.registry._run("query", domain="neuroscience")
        specialist = json.loads(result)
        
        assert specialist['domain'] == 'neuroscience'
        assert 'capabilities' in specialist
    
    def test_availability_update(self):
        """Test updating specialist availability."""
        self.registry._run("update_availability", domain="neuroscience", status="busy")
        
        available = self.registry.get_available_specialists()
        neuroscience = next((s for s in available if s.domain.value == "neuroscience"), None)
        assert neuroscience is None
    
    def test_keyword_matching(self):
        """Test keyword-based specialist discovery."""
        message = "I need help with sleep optimization"
        result = self.registry._run("find_by_keyword", message=message)
        matches = json.loads(result)
        
        assert len(matches) > 0
        assert any(m['domain'] == 'neuroscience' for m in matches)
    
    def test_persistence(self):
        """Test registry persistence."""
        # Update availability
        self.registry._run("update_availability", domain="nutrition", status="busy")
        
        # Create new registry instance
        new_registry = SpecialistRegistry(self.registry_path)
        nutrition = new_registry.get_specialist(SpecialistDomain("nutrition"))
        
        assert nutrition.availability_status == "busy"


class TestPacketBuilder:
    """Test context packet creation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.builder = PacketBuilder(history_limit=5)
    
    def test_packet_creation(self):
        """Test basic packet creation."""
        message = "I need help with sleep"
        routing_decision = {
            'primary_specialist': 'neuroscience',
            'secondary_specialists': [],
            'confidence': 0.85,
            'reasoning': 'Sleep-related keywords detected',
            'requires_collaboration': False,
            'urgency_level': 'normal'
        }
        user_context = {'user_id': 'test_user', 'current_phase': 'optimization'}
        
        result = self.builder._run(message, routing_decision, user_context)
        packet = json.loads(result)
        
        assert packet['original_message'] == message
        assert packet['routing_decision']['primary_specialist'] == 'neuroscience'
        assert 'user_context' in packet
        assert 'timestamp' in packet
    
    def test_collaboration_requests(self):
        """Test collaboration request generation."""
        message = "I have knee pain and need nutrition advice"
        routing_decision = {
            'primary_specialist': 'physical_therapy',
            'secondary_specialists': ['nutrition'],
            'confidence': 0.9,
            'reasoning': 'Multi-domain issue',
            'requires_collaboration': True,
            'urgency_level': 'normal'
        }
        user_context = {'user_id': 'test_user'}
        
        result = self.builder._run(message, routing_decision, user_context)
        packet = json.loads(result)
        
        assert len(packet['collaboration_requests']) > 0
        assert 'nutrition' in str(packet['collaboration_requests'])
    
    def test_urgency_handling(self):
        """Test urgency-based collaboration requests."""
        message = "Urgent: severe knee pain"
        routing_decision = {
            'primary_specialist': 'physical_therapy',
            'secondary_specialists': [],
            'confidence': 0.95,
            'reasoning': 'Urgent pain issue',
            'requires_collaboration': False,
            'urgency_level': 'high'
        }
        user_context = {'user_id': 'test_user'}
        
        result = self.builder._run(message, routing_decision, user_context)
        packet = json.loads(result)
        
        assert any('urgency' in str(req).lower() for req in packet['collaboration_requests'])


class TestIntegration:
    """Test integration between routing tools."""
    
    def test_complete_routing_flow(self):
        """Test complete message routing flow."""
        # Test message
        message = "I can't sleep and my diet might be affecting my workouts"
        
        # Step 1: Check direct routing
        direct_tool = DirectRoutingTool()
        direct_result = direct_tool._run(message)
        direct_decision = json.loads(direct_result)
        
        # Step 2: If no direct request, use routing logic
        if 'status' in direct_decision:
            routing_tool = RoutingLogicTool()
            routing_result = routing_tool._run(message)
            routing_decision = json.loads(routing_result)
            
            # Step 3: Build context packet
            packet_builder = PacketBuilder()
            packet_result = packet_builder._run(
                message, 
                routing_decision, 
                {'user_id': 'test_user'}
            )
            packet = json.loads(packet_result)
            
            # Verify complete flow
            assert 'primary_specialist' in routing_decision
            assert 'message_id' in packet
            assert packet['original_message'] == message
    
    def test_error_handling(self):
        """Test error handling in routing tools."""
        # Test with empty message
        routing_tool = RoutingLogicTool()
        result = routing_tool._run("")
        decision = json.loads(result)
        
        assert decision['primary_specialist'] == 'general'
        assert 'error' not in decision


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
