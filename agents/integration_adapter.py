"""
Integration adapter for zero-downtime migration to modular architecture.
This allows existing code to work unchanged while using modular config.
"""
import os
import sys
import logging
import functools
import json
from jsonschema import validate

logger = logging.getLogger(__name__)
# Load JSON schema for validation
_schema_path = os.path.join(os.path.dirname(__file__), 'schemas', 'roster-schema.json')
with open(_schema_path) as _f:
    NEUROS_SCHEMA = json.load(_f)

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
        
    @functools.lru_cache(maxsize=1)
    def get_config(self):
        """Get NEUROS configuration (modular or legacy) with caching and validation"""
        if self._config is None:
            if self.use_modular:
                try:
                    roster = load_agent_roster()
                    neuros_cfg = roster["agents"].get("NEUROS")
                    if not neuros_cfg:
                        raise RuntimeError("NEUROS not enabled in roster.yaml")
                    # Validate the config with JSON schema
                    validate(instance=neuros_cfg, schema=NEUROS_SCHEMA)
                    self._config = neuros_cfg
                except Exception as e:
                    logger.warning(f"⚠️ Modular config failed, falling back to legacy: {e}")
                    self._config = load_legacy_neuros()
            else:
                self._config = load_legacy_neuros()
        return self._config
    
    def get_legacy_format(self):
        """Get config in legacy format for existing code with metadata"""
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
            
        # Expose metadata
        config["roster_version"] = "1.0"  # Example version
        config["last_updated"] = "2025-07-31"  # Example date
        
        return config

# Global adapter instance
neuros_adapter = NEUROSConfigAdapter(use_modular=True)

# Backward compatibility function
def load_neuros_config():
    """Drop-in replacement for existing NEUROS config loading"""
    return neuros_adapter.get_legacy_format() 