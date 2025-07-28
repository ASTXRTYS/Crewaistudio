# NEUROS YAML Integration Instructions

## For: Senior Engineer
## Re: Integrating NEUROS Agent Profile into Section 8 Implementation

---

## Overview

You'll be receiving a 1,100-line YAML file that defines NEUROS, our Central Nervous System specialist agent. This document explains how to integrate it with the Section 8 Python implementation.

---

## What You're Getting

**File**: `neuros_agent_profile.yaml` (1,100+ lines)
**Purpose**: Complete personality, behavior, and logic definition for NEUROS
**Contains**: 
- 13 phases of cognitive behavior
- 5 cognitive modes with triggers
- Memory architecture specifications
- Protocol library definitions
- Personality traits and communication patterns

---

## Integration Steps

### 1. File Placement
```bash
auren/
├── config/
│   └── agents/
│       └── neuros_agent_profile.yaml  # <-- Place here
├── biometric/
│   └── section_8_neuros_graph.py     # Your implementation file
```

### 2. Key Sections to Extract

The YAML contains these critical sections that need to be parsed and used:

#### A. Cognitive Modes (Phase 2)
```yaml
phase_2_logic:
  cognitive_modes:
    primary_modes:
      - name: baseline
      - name: reflex
      - name: hypothesis
      - name: companion
      - name: sentinel
```
**Used in**: `CognitiveMode` enum and mode handlers

#### B. Mode Switch Triggers (Phase 2)
```yaml
mode_switch_triggers:
  - condition: "HRV drop > 25ms in 48h"
    switch_to: reflex
  - condition: "REM sleep variance > 30%"
    switch_to: hypothesis
```
**Used in**: `_apply_mode_triggers()` method

#### C. Memory Tiers (Phase 7)
```yaml
phase_7_memory:
  adaptive_memory_layering:
    tiering:
      hot_memory:
        lifespan: "24-72 hours"
      warm_memory:
        lifespan: "1-4 weeks"
      cold_memory:
        lifespan: "6 months - 1 year"
```
**Used in**: State management and memory handlers

#### D. Protocol Library (Phase 4)
```yaml
phase_4_logic:
  experimental_protocol_stack:
    structure:
      - protocol_set:
          id: neurostack_alpha
          focus: sleep_latency_reset
```
**Used in**: `_load_protocol_library()` method

#### E. Communication Patterns
```yaml
communication:
  conversation_flow_patterns:
    opening_acknowledgment:
      examples:
        - "Morning. Sleep latency rose 19 minutes..."
```
**Used in**: Response generation in each mode handler

---

## Implementation Requirements

### 3. YAML Loader Enhancement

Add this to the `NEUROSCognitiveGraph.__init__()`:

```python
def __init__(self, llm, postgres_url: str, redis_url: str, neuros_yaml_path: str):
    # ... existing code ...
    
    # Load NEUROS profile
    self.neuros_profile = self._load_neuros_profile(neuros_yaml_path)
    
def _load_neuros_profile(self, yaml_path: str) -> Dict[str, Any]:
    """Load and validate NEUROS YAML profile"""
    try:
        with open(yaml_path, 'r') as f:
            profile = yaml.safe_load(f)
        
        # Validate required sections exist
        required_sections = [
            'agent_profile', 'communication', 'personality',
            'phase_2_logic', 'phase_4_logic', 'phase_7_memory'
        ]
        
        for section in required_sections:
            if section not in profile:
                raise ValueError(f"Missing required section: {section}")
        
        logger.info(f"Loaded NEUROS profile v{profile['agent_profile']['version']}")
        return profile
        
    except Exception as e:
        logger.error(f"Failed to load NEUROS profile: {e}")
        raise
```

### 4. Dynamic Response Generation

Each mode handler should pull response templates from the YAML:

```python
def _get_mode_responses(self, mode: str) -> Dict[str, List[str]]:
    """Get response templates for a specific mode from YAML"""
    flow_patterns = self.neuros_profile['communication']['conversation_flow_patterns']
    
    # Extract examples based on mode
    if mode == "reflex":
        return flow_patterns.get('opening_acknowledgment', {}).get('examples', [])
    # ... etc
```

### 5. Protocol Selection

Use the YAML's protocol library instead of hardcoded protocols:

```python
def _select_protocol(self, focus_area: str) -> Optional[Dict[str, Any]]:
    """Select protocol from YAML based on user's needs"""
    protocols = self.neuros_profile['phase_4_logic']['experimental_protocol_stack']['structure']
    
    for protocol in protocols:
        if protocol['protocol_set']['focus'] == focus_area:
            return protocol['protocol_set']
    
    return None
```

---

## Critical Integration Points

### 6. Personality Traits Usage

The YAML defines personality traits that should influence response generation:

```python
# In each mode handler, reference personality
personality = self.neuros_profile['personality']['key_attributes']
tone = self.neuros_profile['personality']['language_style']

# Use these to shape responses
```

### 7. Multi-Agent Synchronization

Phase 2 includes inter-agent synchronization:
```yaml
collaborative_mode_synchronization:
  inter_agent_mode_alignment:
    - if_mode: sentinel
      sync_with: AUPEX_Physical_Therapist.mode: "posture_watch"
```

**TODO**: Implement agent synchronization in future phases

---

## Testing the Integration

### 8. Validation Script

Create `test_neuros_yaml_integration.py`:

```python
import asyncio
from section_8_neuros_graph import NEUROSCognitiveGraph

async def test_yaml_integration():
    # Initialize with YAML
    neuros = NEUROSCognitiveGraph(
        llm=your_llm,
        postgres_url="postgresql://...",
        redis_url="redis://...",
        neuros_yaml_path="config/agents/neuros_agent_profile.yaml"
    )
    
    await neuros.initialize()
    
    # Test that all modes are loaded
    assert len(neuros.neuros_profile['phase_2_logic']['cognitive_modes']['primary_modes']) == 5
    
    # Test protocol library
    protocols = neuros._load_protocol_library()
    assert 'neurostack_alpha' in protocols
    
    print("✅ YAML integration successful!")

if __name__ == "__main__":
    asyncio.run(test_yaml_integration())
```

---

## Questions for Clarification

Before proceeding, please confirm:

1. **YAML Location**: Should the YAML be in `config/agents/` or elsewhere?
2. **Runtime Loading**: Should the YAML be loaded once at startup or support hot-reloading?
3. **Partial Implementation**: Should we implement all 13 phases immediately or start with phases 2, 4, and 7?
4. **Agent Coordination**: How will NEUROS communicate with other AUREN agents (Nutritionist, Physical Therapist, etc.)?

---

## Next Steps

1. Place the YAML file in the designated location
2. Update the `NEUROSCognitiveGraph` initialization to accept the YAML path
3. Implement the `_load_neuros_profile()` method
4. Update each mode handler to use YAML-defined responses
5. Run the validation script to ensure proper integration

---

## Important Notes

- The YAML is the "source of truth" for NEUROS's personality
- Any hardcoded responses in the Python implementation should be replaced with YAML references
- The YAML defines behavior that goes beyond what's currently implemented - implement phases incrementally
- Some YAML features (like multi-agent sync) require infrastructure not yet built

---

**File this document as**: `docs/implementation/neuros_yaml_integration.md`

Let me know if you need any clarification on integrating the NEUROS personality definition!