#!/usr/bin/env python3
"""
Test script for NEUROS YAML integration
Tests that the YAML profile is loaded correctly and integrated with the cognitive graph
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add the auren/docs/context to path since that's where our implementation is
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auren', 'docs', 'context'))

from neuros_cognitive_graph_v2 import NEUROSCognitiveGraph, CognitiveMode

# Mock LLM for testing
class MockLLM:
    async def ainvoke(self, messages):
        return "Mock response"

async def test_yaml_integration():
    """Test that YAML integration works correctly"""
    
    print("🧪 Testing NEUROS YAML Integration...")
    
    # Paths
    yaml_path = "config/agents/neuros_agent_profile.yaml"
    
    # Check YAML file exists
    if not os.path.exists(yaml_path):
        print(f"❌ YAML file not found at {yaml_path}")
        return False
    
    print(f"✅ Found YAML file at {yaml_path}")
    
    try:
        # Initialize NEUROS with YAML
        neuros = NEUROSCognitiveGraph(
            llm=MockLLM(),
            postgres_url="postgresql://user:pass@localhost/test",  # Mock URL
            redis_url="redis://localhost:6379",  # Mock URL
            neuros_yaml_path=yaml_path
        )
        
        print("✅ NEUROSCognitiveGraph initialized with YAML")
        
        # Test 1: Check YAML was loaded
        assert neuros.neuros_profile is not None, "YAML profile should be loaded"
        print("✅ YAML profile loaded successfully")
        
        # Test 2: Check all required sections exist
        required_sections = [
            'agent_profile', 'communication', 'personality',
            'phase_2_logic', 'phase_4_logic', 'phase_7_memory'
        ]
        
        for section in required_sections:
            assert section in neuros.neuros_profile, f"Missing section: {section}"
        
        print(f"✅ All {len(required_sections)} required sections found")
        
        # Test 3: Check cognitive modes from YAML
        modes = neuros.neuros_profile['phase_2_logic']['cognitive_modes']['primary_modes']
        assert len(modes) == 5, f"Expected 5 modes, found {len(modes)}"
        
        mode_names = [m['name'] for m in modes]
        expected_modes = ['baseline', 'reflex', 'hypothesis', 'companion', 'sentinel']
        for expected in expected_modes:
            assert expected in mode_names, f"Missing mode: {expected}"
        
        print(f"✅ All 5 cognitive modes found: {', '.join(mode_names)}")
        
        # Test 4: Check protocol library
        protocols = neuros._load_protocol_library()
        assert 'neurostack_alpha' in protocols, "Missing neurostack_alpha protocol"
        assert 'neurostack_beta' in protocols, "Missing neurostack_beta protocol"
        assert 'neurostack_gamma' in protocols, "Missing neurostack_gamma protocol"
        
        print(f"✅ Loaded {len(protocols)} protocols from YAML")
        
        # Test 5: Check mode response templates
        baseline_responses = neuros._get_mode_responses('baseline')
        assert 'examples' in baseline_responses, "Missing response examples"
        assert len(baseline_responses['examples']) > 0, "No response examples found"
        
        print(f"✅ Found {len(baseline_responses['examples'])} response templates for baseline mode")
        
        # Test 6: Verify personality attributes
        personality = neuros.neuros_profile['personality']
        assert 'traits' in personality, "Missing personality traits"
        assert 'key_attributes' in personality, "Missing key attributes"
        assert 'language_style' in personality, "Missing language style"
        
        print(f"✅ Personality configuration loaded with {len(personality['traits'])} traits")
        
        # Test 7: Check memory tiers from phase 7
        memory_config = neuros.neuros_profile['phase_7_memory']['adaptive_memory_layering']['tiering']
        assert 'hot_memory' in memory_config, "Missing hot memory tier"
        assert 'warm_memory' in memory_config, "Missing warm memory tier"
        assert 'cold_memory' in memory_config, "Missing cold memory tier"
        
        print("✅ All 3 memory tiers configured")
        
        print("\n🎉 All tests passed! YAML integration successful!")
        print(f"\nNEUROS Profile Summary:")
        print(f"  - Version: {neuros.neuros_profile['agent_profile']['version']}")
        print(f"  - Name: {neuros.neuros_profile['agent_profile']['name']}")
        print(f"  - Model Type: {neuros.neuros_profile['agent_profile']['model_type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_yaml_integration())
    sys.exit(0 if success else 1) 