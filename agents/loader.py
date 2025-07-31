import yaml
import glob
import os
from typing import Dict, Any

def deep_merge(base: dict, override: dict) -> dict:
    """Hierarchical config merging - mirrors Hydra composition pattern"""
    for k, v in override.items():
        if isinstance(v, dict) and k in base:
            base[k] = deep_merge(base[k], v)
        else:
            base[k] = v
    return base

def load_agent_roster() -> Dict[str, Any]:
    """Load and compose complete agent configurations"""
    roster_path = os.path.join(os.path.dirname(__file__), "roster.yaml")
    with open(roster_path) as f:
        roster = yaml.safe_load(f)

    agents = {}
    for name, cfg in roster["agents"].items():
        # Expand include paths using glob patterns
        includes = cfg.get("include", [])
        if isinstance(includes, str):
            includes = [includes]
        
        for pattern in includes:
            pattern_path = os.path.join(os.path.dirname(__file__), pattern)
            for path in glob.glob(pattern_path):
                with open(path) as inc:
                    module_config = yaml.safe_load(inc)
                    if module_config:  # Only merge if module has content
                        cfg = deep_merge(cfg, module_config)
        
        agents[name] = cfg
    
    return {"common": roster.get("common", {}), "agents": agents}

def load_legacy_neuros() -> Dict[str, Any]:
    """Load current working NEUROS configuration for comparison/fallback"""
    legacy_path = os.path.join(os.path.dirname(__file__), "../config/agents/neuros_agent_profile.yaml")
    with open(legacy_path, 'r') as f:
        return yaml.safe_load(f)

# Test function for validation
def test_loader():
    """Quick test to ensure loader works"""
    try:
        config = load_agent_roster()
        print(f"✅ Loaded {len(config['agents'])} agents")
        return True
    except Exception as e:
        print(f"❌ Loader test failed: {e}")
        return False

if __name__ == "__main__":
    test_loader() 