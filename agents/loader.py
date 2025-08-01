import yaml
import glob
import os
import functools
from typing import Dict, Any

def deep_merge(base: dict, override: dict) -> dict:
    """Hierarchical config merging - mirrors Hydra composition pattern"""
    for k, v in override.items():
        if isinstance(v, dict) and k in base:
            base[k] = deep_merge(base[k], v)
        else:
            base[k] = v
    return base

@functools.lru_cache(maxsize=1)
def load_agent_roster() -> Dict[str, Any]:
    """Load and compose complete agent configurations"""
    roster_path = os.path.join(os.path.dirname(__file__), "roster.yaml")
    with open(roster_path) as f:
        roster = yaml.safe_load(f)

    # Validate merge strategy early (prevent surprises if roster changes)
    merge_strategy = roster.get("merge_strategy", "recursive_last_win")
    assert merge_strategy == "recursive_last_win", \
        f"Unsupported merge_strategy: {merge_strategy}. Expected 'recursive_last_win'"

    agents = {}
    skipped_agents = []

    for name, cfg in roster.get("agents", {}).items():
        # Skip disabled agents
        if not cfg.get("enabled", True):
            skipped_agents.append(name)
            print(f"⏭️ Skipping disabled agent: {name} (enabled: false)")
            continue

        # Load base config
        config_copy = cfg.copy()
        includes = config_copy.get("include", [])
        if isinstance(includes, str):
            includes = [includes]
        
        if not includes:
            print(f"⚠️ Agent {name} has no includes, using base config only")
            agents[name] = config_copy
            print(f"✅ Loaded enabled agent: {name} (status: {config_copy.get('status', 'unknown')})")
            continue

        # Merge included module configs in deterministic order
        for pattern in includes:
            pattern_path = os.path.join(os.path.dirname(__file__), pattern)
            for path in sorted(glob.glob(pattern_path)):
                with open(path) as inc:
                    module_config = yaml.safe_load(inc) or {}
                    if module_config:
                        config_copy = deep_merge(config_copy, module_config)

        agents[name] = config_copy
        print(f"✅ Loaded enabled agent: {name} (status: {config_copy.get('status', 'unknown')})")

    metadata = {
        "common": roster.get("common", {}),
        "total_agents": len(roster.get("agents", {})),
        "enabled_agents": len(agents),
        "skipped_agents": skipped_agents,
        "roster_version": roster.get("version", "unknown"),
        "last_updated": roster.get("last_updated", "unknown"),
        "merge_strategy": merge_strategy
    }
    return {"agents": agents, "metadata": metadata, "common": metadata.pop("common")}

def load_legacy_neuros() -> Dict[str, Any]:
    """Load current working NEUROS configuration for comparison/fallback"""
    legacy_path = os.path.join(os.path.dirname(__file__), "../config/agents/neuros_agent_profile.yaml")
    with open(legacy_path, 'r') as f:
        return yaml.safe_load(f)

# Enhanced test function with validation
def test_loader():
    """Test the agent roster loading functionality with enhanced validation"""
    print("🧪 Testing Enhanced Agent Roster Loader...")
    print("=" * 45)
    
    try:
        config = load_agent_roster()
        
        print(f"✅ Loader executed successfully")
        print(f"📊 Total agents: {config['metadata']['total_agents']}")
        print(f"🟢 Enabled agents: {config['metadata']['enabled_agents']}")
        print(f"⏭️ Skipped agents: {len(config['metadata']['skipped_agents'])}")
        print(f"📋 Roster version: {config['metadata']['roster_version']}")
        print(f"📅 Last updated: {config['metadata']['last_updated']}")
        print(f"🔀 Merge strategy: {config['metadata']['merge_strategy']}")
        
        if config['metadata']['skipped_agents']:
            print(f"   Skipped: {', '.join(config['metadata']['skipped_agents'])}")
        
        # Verify NEUROS is present and enabled
        if "NEUROS" in config["agents"]:
            neuros = config["agents"]["NEUROS"]
            print(f"✅ NEUROS agent loaded (status: {neuros.get('status', 'unknown')})")
            print(f"   Role: {neuros.get('role', 'unknown')}")
            print(f"   Includes: {len(neuros.get('include', []))} modules")
            
            # Enhanced validation: Verify Kafka topic naming (Confluent guidelines)
            topics_to_check = ['ingest_topic', 'output_topic', 'status_topic']
            for topic_key in topics_to_check:
                if topic_key in neuros:
                    topic = neuros[topic_key]
                    assert "neuros" in topic.lower(), \
                        f"NEUROS {topic_key} should contain 'neuros', got: {topic}"
                    print(f"✅ Kafka topic validation passed: {topic}")
            
            # Verify deep merge worked (should have properties from included modules)
            if "personality" in neuros:
                print(f"✅ Deep merge validation: personality config loaded")
            elif "voice_characteristics" in neuros:
                print(f"✅ Deep merge validation: voice_characteristics config loaded")
            else:
                print(f"⚠️ Deep merge check: No merged personality data found")
            
        else:
            print("❌ NEUROS agent not found!")
            return False
        
        print(f"\n🎉 Enhanced agent roster loading test completed successfully!")
        print(f"🛡️ All edge-case protections active:")
        print(f"   • Empty YAML protection (returns {{}} not None)")
        print(f"   • Deterministic merge order (sorted glob results)")
        print(f"   • Merge strategy validation")
        print(f"   • LRU cache for performance")
        return True
        
    except Exception as e:
        print(f"❌ Loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_loader() 