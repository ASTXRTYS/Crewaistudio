# AUREN Cognitive Twin Profile - Complete Implementation

## Overview

This is the complete implementation of AUREN's Cognitive Twin Profile - the foundation of long-term memory that tracks biological optimization patterns over months and years. This is NOT a 30-day chatbot; this is a system that remembers everything and gets smarter over time.

## Architecture Components

### 1. Core Memory Layer (`src/memory/cognitive_twin_profile.py`)
- **CognitiveTwinProfile**: The persistent profile that makes AUREN truly know the user
- **BiometricEntry**: Represents individual measurements (DEXA, bloodwork, weight, energy, sleep, etc.)
- **Milestone**: Significant achievements or events in the optimization journey
- **Pattern Insights**: Scientific analysis of what works for THIS specific user

### 2. Service Layer (`src/services/cognitive_twin_service.py`)
- **CognitiveTwinService**: Clean API layer between AUREN and the memory system
- **Natural Language Processing**: Extracts biometrics from conversation
- **User-friendly responses**: Maintains AUREN's warm personality

### 3. Database Layer (`src/core/database.py`)
- **PostgreSQL with asyncpg**: Handles months/years of data
- **Connection pooling**: Optimized for high performance
- **Schema**: Designed for long-term storage and pattern recognition

### 4. Integration Layer (`src/agents/auren_with_cognitive.py`)
- **Seamless integration**: AUREN tracks biometrics without breaking conversation flow
- **Contextual responses**: Uses tracked data to provide personalized insights

## Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp .env.template .env

# Edit .env with your database configuration
# Option 1: Single DATABASE_URL (recommended)
DATABASE_URL=postgresql://user:password@localhost:5432/auren

# Option 2: Individual components
DB_HOST=localhost
DB_PORT=5432
DB_NAME=auren
DB_USER=auren
DB_PASSWORD=auren
```

### 2. Database Setup
```bash
# Run the setup script
python setup_cognitive_twin.py
```

### 3. Test the Integration
```bash
# Run the demo
python demo_cognitive_service.py
```

## Usage Examples

### Basic Weight Tracking
```python
import asyncio
from auren.src.services.cognitive_twin_service import CognitiveTwinService
from auren.src.core.database import db

async def track_weight():
    await db.initialize()
    service = CognitiveTwinService(db.pool)
    
    # Track weight with natural language
    result = await service.track_weight("user_123", 218.5, "lbs")
    print(result.message)  # "Got it! I've recorded your weight as 218.5 lbs..."
    
    # Get insights
    insights = await service.get_weight_insights("user_123")
    print(insights.message)  # "Here's what I've noticed about your weight..."
```

### Natural Language Extraction
```python
# AUREN can extract data from natural conversation
service = CognitiveTwinService(None)  # No DB needed for extraction

# Extract from text
weight = service.extract_weight_from_text("I weighed 215 lbs this morning")
# Returns: {"weight": 215.0, "unit": "lbs"}

energy = service.extract_energy_from_text("Energy is 8 out of 10 today")
# Returns: 8

sleep = service.extract_sleep_from_text("Got 8 hours of sleep last night")
# Returns: {"hours": 8.0, "quality": 5}
```

### AUREN Integration
```python
from auren.src.agents.auren_with_cognitive import AURENWithCognitive

auren = AURENWithCognitive("user_123")
await auren.initialize()

# AUREN automatically tracks biometrics from conversation
response = await auren.process_message_with_tracking(
    "Good morning! I weighed 218.5 lbs and got 8 hours of sleep"
)
# AUREN responds naturally while tracking the data
```

## Supported Biometric Types

### Weight Tracking
- **Units**: lbs, kg
- **Natural language**: "I weighed 218.5 lbs", "Down to 215 pounds"
- **Insights**: Weight loss rate, trends over time

### Energy Tracking
- **Scale**: 1-10
- **Natural language**: "Energy is 8 out of 10", "Feeling great today"
- **Insights**: Morning energy patterns, correlations

### Sleep Tracking
- **Metrics**: Hours, quality (1-10)
- **Natural language**: "Got 8 hours of sleep", "Slept for 7.5 hours"
- **Insights**: Sleep quality impact on energy

### Milestone Tracking
- **Categories**: weight_loss, strength_gain, energy_optimization, etc.
- **Impact metrics**: Quantified achievements
- **Examples**: "Lost 5 lbs in 2 weeks", "Hit new PR on bench press"

## Database Schema

### user_profiles
- `user_id` (PRIMARY KEY)
- `profile_data` (JSONB) - User preferences and settings
- `preference_evolution` (JSONB) - How preferences change over time
- `optimization_history` (JSONB) - Complete optimization timeline

### biometric_timeline
- `id` (SERIAL PRIMARY KEY)
- `user_id` (FOREIGN KEY)
- `timestamp` - When measurement was taken
- `measurement_type` - Type of biometric (weight, energy, sleep, etc.)
- `data` (JSONB) - Actual measurement data
- `metadata` (JSONB) - Additional context

### milestones
- `id` (SERIAL PRIMARY KEY)
- `user_id` (FOREIGN KEY)
- `timestamp` - When milestone was achieved
- `category` - Type of milestone
- `title` - Human-readable title
- `description` - Detailed description
- `impact_metrics` (JSONB) - Quantified impact
- `tags` - Array of tags for categorization

## Pattern Recognition

The system identifies patterns specific to each user:

### Weight Loss Patterns
- **Rate analysis**: Average lbs/week over timeframes
- **Correlation discovery**: What interventions lead to weight changes
- **Confidence scoring**: More data = higher confidence

### Energy Optimization
- **Morning energy patterns**: How energy varies by time of day
- **Intervention correlation**: What affects energy levels
- **Predictive insights**: Based on historical patterns

### Sleep Impact Analysis
- **Sleep quality vs energy**: How sleep affects next-day energy
- **Duration optimization**: Optimal sleep duration for this user
- **Timing patterns**: Best sleep/wake times

## Testing

### Unit Tests
```bash
# Run integration tests
python -m pytest tests/test_cognitive_integration.py -v
```

### Manual Testing
```bash
# Run the demo
python demo_cognitive_service.py

# Run AUREN integration demo
python src/agents/auren_with_cognitive.py
```

## Architecture Benefits

### 1. Long-term Memory
- **Months/years of data**: Not limited to 30 days
- **Compound knowledge**: More data = exponentially greater value
- **Scientific approach**: Hypothesis testing and validation

### 2. Personalization
- **User-specific patterns**: What works for THIS individual
- **Contextual insights**: Based on complete history
- **Natural interaction**: Feels like a knowledgeable friend

### 3. Scalability
- **Async operations**: All database calls are async
- **Connection pooling**: Optimized for performance
- **Clean architecture**: Easy to extend and maintain

## Next Steps

1. **Temporal RAG**: Implement intelligent retrieval across time
2. **Specialist Integration**: Connect with federated specialist system
3. **Compound Memory Engine**: Add hypothesis testing and validation
4. **Visual Integration**: Connect with MIRAGE protocol for visual tracking

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:password@host:5432/auren

# Optional
DB_HOST=localhost
DB_PORT=5432
DB_NAME=auren
DB_USER=auren
DB_PASSWORD=auren
DB_SSL_MODE=prefer
```

## Troubleshooting

### Database Connection Issues
1. Ensure PostgreSQL is running
2. Check DATABASE_URL format
3. Verify user has CREATE TABLE permissions
4. Check firewall settings for remote databases

### Import Errors
1. Install dependencies: `pip install -r requirements.txt`
2. Ensure Python 3.10+ is being used
3. Check virtual environment is activated

### Testing Issues
1. Ensure test database is accessible
2. Check if DATABASE_URL points to test database
3. Verify asyncpg is installed: `pip install asyncpg`

## Support

This is the foundation of AUREN's long-term memory system. For questions or issues, refer to the main AUREN documentation or create an issue in the repository.
