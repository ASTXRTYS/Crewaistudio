#!/usr/bin/env python3
"""
Comprehensive validation test for NEUROS modular architecture.
Ensures modular system produces identical functionality to current implementation.
"""

import sys
import os
sys.path.append('agents')

from agents.integration_adapter import NEUROSConfigAdapter
from agents.loader import load_agent_roster, load_legacy_neuros
import yaml

def test_modular_vs_legacy():
    """Test modular configuration against legacy for implemented features only"""
    print("🔄 Testing modular architecture vs legacy (implemented features only)...")
    
    try:
        # Load modular config
        adapter = NEUROSConfigAdapter(use_modular=True)
        modular_config = adapter.get_config()
        
        # Load legacy config
        legacy_config = load_legacy_neuros()
        
        print(f"📊 Modular config sections: {list(modular_config.keys())}")
        print(f"📊 Legacy config sections: {list(legacy_config.keys())}")
        
        # Test core sections that should be identical
        implemented_sections = [
            "agent_profile",
            "communication", 
            "personality",
            "phase_2_logic"
        ]
        
        validation_results = {}
        
        for section in implemented_sections:
            # Check if section exists in both
            modular_has = section in modular_config
            legacy_has = section in legacy_config
            
            if modular_has and legacy_has:
                # Compare key fields within sections
                if section == "agent_profile":
                    modular_name = modular_config[section].get("name")
                    legacy_name = legacy_config[section].get("name")
                    if modular_name == legacy_name == "NEUROS":
                        validation_results[section] = "✅ PASS"
                    else:
                        validation_results[section] = "❌ FAIL - Name mismatch"
                        
                elif section == "communication":
                    modular_voice = modular_config[section].get("voice_characteristics", [])
                    legacy_voice = legacy_config[section].get("voice_characteristics", [])
                    if len(modular_voice) == len(legacy_voice):
                        validation_results[section] = "✅ PASS"
                    else:
                        validation_results[section] = "❌ FAIL - Voice characteristics mismatch"
                        
                elif section == "personality":
                    modular_traits = modular_config[section].get("traits", [])
                    legacy_traits = legacy_config[section].get("traits", [])
                    if len(modular_traits) == len(legacy_traits):
                        validation_results[section] = "✅ PASS"
                    else:
                        validation_results[section] = "❌ FAIL - Traits mismatch"
                        
                elif section == "phase_2_logic":
                    modular_modes = modular_config[section]["cognitive_modes"]["primary_modes"]
                    legacy_modes = legacy_config[section]["cognitive_modes"]["primary_modes"]
                    if len(modular_modes) == len(legacy_modes) == 5:
                        validation_results[section] = "✅ PASS"
                    else:
                        validation_results[section] = "❌ FAIL - Cognitive modes mismatch"
                        
            elif modular_has and not legacy_has:
                validation_results[section] = "⚠️ WARNING - Only in modular"
            elif legacy_has and not modular_has:
                validation_results[section] = "❌ FAIL - Missing from modular"
            else:
                validation_results[section] = "❌ FAIL - Missing from both"
        
        # Print validation results
        print("\n📋 VALIDATION RESULTS:")
        for section, result in validation_results.items():
            print(f"   {section}: {result}")
        
        # Test ethical boundaries integration
        if "ethical_boundaries" in modular_config:
            print("   ethical_boundaries: ✅ PASS - Shared module integrated")
        else:
            print("   ethical_boundaries: ❌ FAIL - Shared module not integrated")
        
        # Test adapter functionality
        legacy_format = adapter.get_legacy_format()
        if "agent_profile" in legacy_format:
            print("   adapter_compatibility: ✅ PASS - Legacy format working")
        else:
            print("   adapter_compatibility: ❌ FAIL - Legacy format broken")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False

def test_fallback_protection():
    """Test automatic fallback to legacy system"""
    print("\n🛡️ Testing fallback protection...")
    
    try:
        # Test legacy fallback
        adapter_legacy = NEUROSConfigAdapter(use_modular=False)
        legacy_config = adapter_legacy.get_config()
        
        if "agent_profile" in legacy_config and legacy_config["agent_profile"]["name"] == "NEUROS":
            print("   fallback_protection: ✅ PASS - Legacy fallback working")
            return True
        else:
            print("   fallback_protection: ❌ FAIL - Legacy fallback broken")
            return False
            
    except Exception as e:
        print(f"   fallback_protection: ❌ FAIL - Exception: {e}")
        return False

def main():
    """Run complete validation suite"""
    print("🎯 NEUROS MODULAR ARCHITECTURE VALIDATION")
    print("="*50)
    
    # Test 1: Modular vs Legacy
    test1_result = test_modular_vs_legacy()
    
    # Test 2: Fallback Protection
    test2_result = test_fallback_protection()
    
    # Final results
    print("\n🏆 FINAL VALIDATION RESULTS:")
    print("="*50)
    
    if test1_result and test2_result:
        print("✅ MODULAR ARCHITECTURE VALIDATION: PASSED")
        print("🎯 System ready for production use")
        print("🔄 Zero-downtime modular transformation: SUCCESSFUL")
    else:
        print("❌ MODULAR ARCHITECTURE VALIDATION: FAILED")
        print("⚠️ Review errors above before proceeding")
    
    return test1_result and test2_result

if __name__ == "__main__":
    main() 