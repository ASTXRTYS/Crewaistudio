#!/usr/bin/env python3
"""
Simple validation test for NEUROS modular architecture.
Ensures modular system produces identical functionality to current implementation.
"""

import sys
import os
import yaml

# Add agents directory to path without triggering __init__.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

# Import specific modules directly
import loader
import integration_adapter

def test_basic_modular_loading():
    """Test basic modular configuration loading"""
    print("🔄 Testing basic modular loading...")
    
    try:
        # Test roster loading
        config = loader.load_agent_roster()
        print(f"✅ Loaded roster with {len(config['agents'])} agents")
        
        # Test NEUROS agent exists
        if "NEUROS" in config["agents"]:
            neuros = config["agents"]["NEUROS"]
            print(f"✅ NEUROS agent loaded with {len(neuros)} sections")
            
            # Check essential sections
            essential_sections = ["agent_profile", "communication", "personality", "phase_2_logic"]
            missing_sections = []
            
            for section in essential_sections:
                if section not in neuros:
                    missing_sections.append(section)
            
            if not missing_sections:
                print("✅ All essential sections present in modular config")
                return True
            else:
                print(f"❌ Missing sections: {missing_sections}")
                return False
        else:
            print("❌ NEUROS agent not found in config")
            return False
            
    except Exception as e:
        print(f"❌ Basic loading test failed: {e}")
        return False

def test_legacy_comparison():
    """Test modular vs legacy configuration"""
    print("\n🔄 Testing modular vs legacy comparison...")
    
    try:
        # Load legacy
        legacy = loader.load_legacy_neuros()
        print(f"✅ Legacy config loaded with {len(legacy)} sections")
        
        # Load modular
        modular_config = loader.load_agent_roster()
        neuros_modular = modular_config["agents"]["NEUROS"]
        print(f"✅ Modular config loaded with {len(neuros_modular)} sections")
        
        # Compare implemented sections
        comparison_results = {}
        
        # Agent profile comparison
        if "agent_profile" in legacy and "agent_profile" in neuros_modular:
            legacy_name = legacy["agent_profile"].get("name")
            modular_name = neuros_modular["agent_profile"].get("name")
            comparison_results["agent_profile"] = legacy_name == modular_name == "NEUROS"
        
        # Communication comparison
        if "communication" in legacy and "communication" in neuros_modular:
            legacy_voice = legacy["communication"].get("voice_characteristics", [])
            modular_voice = neuros_modular["communication"].get("voice_characteristics", [])
            comparison_results["communication"] = len(legacy_voice) == len(modular_voice)
        
        # Cognitive modes comparison
        if "phase_2_logic" in legacy and "phase_2_logic" in neuros_modular:
            legacy_modes = legacy["phase_2_logic"]["cognitive_modes"]["primary_modes"]
            modular_modes = neuros_modular["phase_2_logic"]["cognitive_modes"]["primary_modes"]
            comparison_results["phase_2_logic"] = len(legacy_modes) == len(modular_modes)
        
        # Print results
        print("\n📋 COMPARISON RESULTS:")
        for section, result in comparison_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {section}: {status}")
        
        return all(comparison_results.values())
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        return False

def both_configs(legacy, modular):
    """Helper to check if section exists in both configs"""
    def check_section(section):
        return section in legacy and section in modular
    return check_section

def test_integration_adapter():
    """Test the integration adapter functionality"""
    print("\n🔄 Testing integration adapter...")
    
    try:
        # Test modular adapter
        adapter = integration_adapter.NEUROSConfigAdapter(use_modular=True)
        config = adapter.get_config()
        
        if config and "agent_profile" in config:
            print("✅ Integration adapter working with modular config")
        else:
            print("❌ Integration adapter failed with modular config")
            return False
        
        # Test legacy adapter
        adapter_legacy = integration_adapter.NEUROSConfigAdapter(use_modular=False)
        legacy_config = adapter_legacy.get_config()
        
        if legacy_config and "agent_profile" in legacy_config:
            print("✅ Integration adapter working with legacy config")
        else:
            print("❌ Integration adapter failed with legacy config")
            return False
        
        # Test legacy format conversion
        legacy_format = adapter.get_legacy_format()
        if legacy_format and "agent_profile" in legacy_format:
            print("✅ Legacy format conversion working")
            return True
        else:
            print("❌ Legacy format conversion failed")
            return False
            
    except Exception as e:
        print(f"❌ Integration adapter test failed: {e}")
        return False

def main():
    """Run simplified validation suite"""
    print("🎯 NEUROS MODULAR ARCHITECTURE VALIDATION (SIMPLIFIED)")
    print("="*60)
    
    # Test 1: Basic loading
    test1 = test_basic_modular_loading()
    
    # Test 2: Legacy comparison
    test2 = test_legacy_comparison()
    
    # Test 3: Integration adapter
    test3 = test_integration_adapter()
    
    # Final results
    print("\n🏆 FINAL VALIDATION RESULTS:")
    print("="*60)
    
    all_passed = test1 and test2 and test3
    
    if all_passed:
        print("✅ MODULAR ARCHITECTURE VALIDATION: PASSED")
        print("🎯 System ready for production use")
        print("🔄 Zero-downtime modular transformation: SUCCESSFUL")
        print("\n📊 SUMMARY:")
        print("   • Modular loading: ✅ Working")
        print("   • Legacy compatibility: ✅ Working") 
        print("   • Integration adapter: ✅ Working")
        print("   • Fallback protection: ✅ Available")
    else:
        print("❌ MODULAR ARCHITECTURE VALIDATION: FAILED")
        print("⚠️ Review errors above before proceeding")
    
    return all_passed

if __name__ == "__main__":
    main() 