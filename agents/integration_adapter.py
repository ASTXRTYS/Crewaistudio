"""
Integration adapter for zero-downtime migration to modular architecture.
This allows existing code to work unchanged while using modular config.
"""
import os
import sys

# Add agents directory to path
agents_path = os.path.join(os.path.dirname(__file__))
if agents_path not in sys.path:
    sys.path.insert(0, agents_path)

from loader import load_agent_roster, load_legacy_neuros

class NEUROSConfigAdapter:
    """Provides backward-compatible interface to modular NEUROS config"""
    
    def __init__(self, use_modular=True):
        self.use_modular = use_modular
        self._config = None
        
    def get_config(self):
        """Get NEUROS configuration (modular or legacy)"""
        if self._config is None:
            if self.use_modular:
                try:
                    roster = load_agent_roster()
                    self._config = roster["agents"]["NEUROS"]
                except Exception as e:
                    print(f"⚠️ Modular config failed, falling back to legacy: {e}")
                    self._config = load_legacy_neuros()
            else:
                self._config = load_legacy_neuros()
        
        return self._config
    
    def get_legacy_format(self):
        """Get config in legacy format for existing code"""
        config = self.get_config()
        
        # Ensure backward compatibility with existing code
        if "agent_profile" not in config:
            # If modular structure, extract agent_profile section
            agent_profile = {
                "name": "NEUROS",
                "model_type": "Elite cognitive and biometric optimization agent",
                "background_story": config.get("role", "Central Nervous System Specialist")
            }
            config["agent_profile"] = agent_profile
            
        return config

# Global adapter instance
neuros_adapter = NEUROSConfigAdapter(use_modular=True)

# Backward compatibility function
def load_neuros_config():
    """Drop-in replacement for existing NEUROS config loading"""
    return neuros_adapter.get_legacy_format() 