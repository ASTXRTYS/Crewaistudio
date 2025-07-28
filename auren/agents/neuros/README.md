# NEUROS - Cognitive Neuroscience Optimization Agent

## Overview

NEUROS is the world's first biometric-aware AI personality system that adapts its behavior based on real-time physiological signals. This directory contains all components of the NEUROS implementation.

## Directory Structure

```
neuros/
├── README.md                           # This file
├── neuros_agent_profile.yaml          # Complete YAML personality profile (13 phases)
├── section_8_neuros_graph.py          # LangGraph implementation with checkpointing
├── requirements.txt                   # Python dependencies
├── tests/                            # Test suites
│   ├── test_neuros_integration.py
│   └── test_yaml_validation.py
├── deployment/                       # Deployment configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── kubernetes/
└── docs/                            # Additional documentation
    ├── INTEGRATION_GUIDE.md
    └── API_REFERENCE.md
```

## Key Features

### 🧠 5 Cognitive Modes

1. **BASELINE** - Default observation and trend-tracking
2. **REFLEX** - Rapid response to biometric anomalies (HRV drop > 25ms)
3. **HYPOTHESIS** - Active pattern analysis mode
4. **COMPANION** - Supportive mode for emotional states
5. **SENTINEL** - High-alert monitoring for critical states

### 📊 Biometric Triggers

- HRV drop > 25ms → REFLEX mode
- REM variance > 30% → HYPOTHESIS mode
- "I feel off" → COMPANION mode
- High stress + elevated HR → SENTINEL mode

### 🗄️ 3-Tier Memory Architecture

- **Hot Memory** (24-72 hours) - Recent events and immediate context
- **Warm Memory** (1-4 weeks) - Pattern tracking and adaptations
- **Cold Memory** (6 months-1 year) - Long-term behavioral baselines

### 📚 Protocol Library

- **neurostack_alpha** - Sleep latency reset (7 days)
- **neurostack_beta** - Mid-day cognitive surge (5 days)
- **neurostack_gamma** - Stress recoding loop (10 days)

## Integration Points

### Biometric Bridge (Section 7)
```python
from neuros.section_8_neuros_graph import NEUROSCognitiveGraph

# Initialize
neuros = NEUROSCognitiveGraph(
    llm=your_llm,
    postgres_url="postgresql://...",
    redis_url="redis://...",
    neuros_yaml_path="neuros_agent_profile.yaml"
)

# Process biometric event
response = await neuros.process_biometric_event(event, thread_id)
```

### Real-time Mode Switching
- Processes Kafka biometric events
- Switches personality in <2 seconds
- Maintains state across sessions via PostgreSQL checkpointing

## Performance Specifications

- **Response Time**: <2 seconds from biometric event to personality switch
- **Checkpointing**: Async PostgreSQL with retry policies
- **Concurrency**: Thread-safe with processing locks
- **Memory Management**: Automatic pruning of old memories

## Deployment

See `deployment/` directory for:
- Docker containerization
- Kubernetes manifests
- Environment configuration
- Health check endpoints

## Testing

Run tests with:
```bash
pytest tests/test_neuros_integration.py
python tests/test_yaml_validation.py
```

## Configuration

All personality configuration is in `neuros_agent_profile.yaml`:
- Edit cognitive modes and triggers
- Modify response templates
- Adjust memory tier durations
- Add new protocols

## Status

✅ **PRODUCTION READY** - Passed 3 rounds of expert review
- All linter errors fixed
- YAML integration complete
- Test coverage implemented
- Ready for staging deployment

## Contact

Lead: NEUROS Cognitive Architecture Team
Framework: AUREN (Adaptive User Response Enhancement Network) 