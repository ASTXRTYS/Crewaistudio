#!/usr/bin/env python3
"""
Simple YAML validation test - no imports from the project
"""

import yaml
import os

def test_yaml_structure():
    """Test that the YAML file has the correct structure"""
    
    print("🧪 Testing NEUROS YAML Structure...")
    
    yaml_path = "config/agents/neuros_agent_profile.yaml"
    
    if not os.path.exists(yaml_path):
        print(f"❌ YAML file not found at {yaml_path}")
        return False
    
    print(f"✅ Found YAML file at {yaml_path}")
    
    try:
        # Load YAML
        with open(yaml_path, 'r') as f:
            profile = yaml.safe_load(f)
        
        print("✅ YAML file is valid")
        
        # Check required sections
        required_sections = [
            'agent_profile', 'communication', 'personality',
            'phase_2_logic', 'phase_4_logic', 'phase_7_memory'
        ]
        
        for section in required_sections:
            if section not in profile:
                print(f"❌ Missing section: {section}")
                return False
        
        print(f"✅ All {len(required_sections)} required sections found")
        
        # Check cognitive modes
        modes = profile['phase_2_logic']['cognitive_modes']['primary_modes']
        print(f"✅ Found {len(modes)} cognitive modes:")
        for mode in modes:
            print(f"   - {mode['name']}: {mode['function']}")
        
        # Check protocols
        protocols = profile['phase_4_logic']['experimental_protocol_stack']['structure']
        print(f"\n✅ Found {len(protocols)} protocol stacks:")
        for p in protocols:
            protocol = p['protocol_set']
            print(f"   - {protocol['id']}: {protocol['focus']} ({protocol['duration']})")
        
        # Check memory tiers
        memory_tiers = profile['phase_7_memory']['adaptive_memory_layering']['tiering']
        print(f"\n✅ Found {len(memory_tiers)} memory tiers:")
        for tier_name, tier_config in memory_tiers.items():
            print(f"   - {tier_name}: {tier_config['lifespan']}")
        
        # Profile summary
        print(f"\n📋 NEUROS Profile Summary:")
        print(f"   - Name: {profile['agent_profile']['name']}")
        print(f"   - Version: {profile['agent_profile']['version']}")
        print(f"   - Model Type: {profile['agent_profile']['model_type']}")
        print(f"   - Specializations: {len(profile['agent_profile']['specialization'])}")
        
        print("\n🎉 YAML structure validation passed!")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ YAML parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = test_yaml_structure()
    sys.exit(0 if success else 1) 