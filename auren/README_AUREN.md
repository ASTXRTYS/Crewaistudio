# AUREN - Cognitive Twin Interface

## Overview
AUREN is the warm, intelligent personality that serves as the primary interface for users. She remembers everything, learns patterns specific to each individual, and provides deeply personalized optimization guidance based on months/years of data.

## Architecture

### Core Components
- **AUREN Class**: Main cognitive twin interface (`ui_orchestrator.py`)
- **SimpleAUREN**: Lightweight version for testing (`ui_orchestrator_simple.py`)
- **Configuration**: YAML-based personality configuration (`config/agents/ui_orchestrator.yaml`)
- **Tests**: Comprehensive test suite (`tests/test_ui_orchestrator.py`)

### Memory Layers
- **Immediate**: Redis for short-term context (last 30 days)
- **Long-term**: PostgreSQL for permanent storage (months/years)
- **Knowledge Graph**: ChromaDB for pattern relationships

## Features

### 1. Contextual Intelligence
- **Personalized Greetings**: Time-aware greetings with workout recovery status
- **Historical Awareness**: References specific past data and patterns
- **Pattern Recognition**: Identifies what works for each individual user

### 2. Intent-Based Responses
- **Nutrition Queries**: Personalized meal recommendations based on historical data
- **Workout Guidance**: Training volume and recovery recommendations
- **Progress Tracking**: Celebrates milestones with journey context
- **General Conversations**: Provides optimization insights

### 3. Natural Interaction
- **Conversational Flow**: Feels like talking to a knowledgeable friend
- **Scientific Approach**: Uses data-driven insights, not generic advice
- **Celebration & Accountability**: Tracks and celebrates every win

## Usage

### Quick Start (Simple Version)
```python
import asyncio
from src.agents.ui_orchestrator_simple import create_simple_auren

async def main():
    auren = await create_simple_auren("your_user_id")
    
    # Start conversation
    response = await auren.process_message("Good morning")
    print(response)
    
    # Nutrition query
    response = await auren.process_message("What should I eat for breakfast?")
    print(response)

asyncio.run(main())
```

### Full Version (with dependencies)
```python
import asyncio
from src.agents.ui_orchestrator import create_auren

async def main():
    auren = await create_auren("your_user_id")
    
    # Process messages with full memory integration
    response = await auren.process_message("How's my progress?")
    print(response)
    
    # Get comprehensive summary
    summary = await auren.get_comprehensive_summary()
    print(summary)

asyncio.run(main())
```

## Configuration

The AUREN personality is configured via `/config/agents/ui_orchestrator.yaml`:

```yaml
ui_orchestrator:
  name: "AUREN"
  role: "Personal Optimization Companion"
  goal: "Guide users through their biological optimization journey..."
  backstory: "Created to solve AI assistants forgetting after 30 days..."
  attributes:
    - Warm and encouraging personality
    - Deep historical awareness
    - Pattern recognition expertise
    - Scientific approach to optimization
```

## Testing

### Run Simple Demo
```bash
cd auren
python src/agents/ui_orchestrator_simple.py
```

### Run Tests (when dependencies available)
```bash
cd auren
python -m pytest tests/test_ui_orchestrator.py -v
```

## Example Interactions

### Morning Greeting
```
User: "Good morning"
AUREN: "Good morning! I see you're up a bit earlier than usual - that's great! 
Based on your energy patterns, early morning workouts have consistently given 
you the best results. Your CNS recovery from Tuesday's session looks good. 
How are you feeling today?"
```

### Nutrition Query
```
User: "What should I eat for breakfast?"
AUREN: "Looking at your recent patterns, you've had the best energy levels and 
workout performance when you have that protein-forward breakfast with moderate 
carbs - similar to what worked so well for you last Thursday. Based on your 
data, aim for 40g protein, 30g carbs, and 15g fat."
```

### Progress Check
```
User: "How's my progress?"
AUREN: "Amazing progress! You've lost 12lbs of fat while gaining 8lbs of lean 
mass since we started tracking. Your strength gains have been incredible: 
Bench Press: +37% (185lbs vs 135lbs), Squat: +22% (225lbs vs 185lbs)"
```

## Development Status

✅ **Completed:**
- Core AUREN interface implementation
- Simple version for testing
- Configuration files
- Comprehensive test suite
- Documentation and examples

🔄 **Next Steps:**
- Integrate with actual memory systems (Redis, PostgreSQL, ChromaDB)
- Connect specialist coordination system
- Add protocol management integration
- Implement real pattern analysis

## Key Design Principles

1. **Memory is Everything**: Every interaction contributes to long-term learning
2. **Personalization First**: No generic advice - everything based on user data
3. **Scientific Method**: Hypothesis testing and validation for all insights
4. **Natural Conversation**: Feels like a knowledgeable friend, not a bot
5. **Compound Knowledge**: More data over time = exponentially greater value

## Architecture Integration

AUREN serves as the primary interface layer that:
- Coordinates with specialist systems (neuroscientist, nutritionist, etc.)
- Manages protocol interactions (Journal, MIRAGE, VISOR)
- Provides seamless user experience across all optimization domains
- Maintains consistent personality while accessing deep expertise
