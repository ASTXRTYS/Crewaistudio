# AUREN Cognitive Twin Profile - Core Memory Foundation

## Overview
The Cognitive Twin Profile is the foundation of AUREN's long-term memory system. Unlike traditional chatbots that forget everything after 30 days, this system tracks biological optimization patterns over **months and years**.

## Key Features

### 🧠 Long-term Memory Storage
- **Persistent storage** of all biometric data
- **Pattern recognition** over extended timeframes
- **Milestone tracking** for significant achievements
- **Preference evolution** tracking for personalization

### 📊 Biometric Tracking
Supports 9 measurement types:
- **DEXA** - Body composition scans
- **BLOODWORK** - Lab results and biomarkers
- **MEASUREMENTS** - Body measurements (waist, chest, etc.)
- **WEIGHT** - Daily weight tracking
- **PHOTO** - Progress photos
- **ENERGY** - Daily energy levels
- **SLEEP** - Sleep quality and duration
- **PTOSIS** - CNS fatigue indicators
- **INFLAMMATION** - Recovery markers

### 🔍 Pattern Recognition
- **Weight loss patterns** - Rate analysis over time
- **Energy optimization** - Correlation with interventions
- **Sleep patterns** - Quality vs performance
- **Custom pattern discovery** - User-specific insights

## Files Structure

### Core Implementation
- `cognitive_twin_profile.py` - Main Cognitive Twin class (PostgreSQL)
- `setup_database.py` - PostgreSQL schema setup for all 4 phases
- `__init__.py` - Module exports

### Testing & Demonstration
- `test_cognitive_twin_sqlite.py` - SQLite demo (no PostgreSQL required)
- `test_cognitive_twin.py` - PostgreSQL demo (requires database)

## Quick Start

### Option 1: SQLite Demo (Recommended for testing)
```bash
cd auren/src/memory
python test_cognitive_twin_sqlite.py
```

### Option 2: PostgreSQL Setup
```bash
# Install dependencies
pip install asyncpg

# Setup database
python setup_database.py --create-test-user

# Run demo
python test_cognitive_twin.py
```

## Usage Examples

### Creating a User Profile
```python
from cognitive_twin_profile import CognitiveTwinProfile, BiometricEntry, BiometricType

# Initialize
twin = CognitiveTwinProfile("user_123", db_pool)
await twin.initialize()

# Add weight measurement
weight_entry = BiometricEntry(
    user_id="user_123",
    timestamp=datetime.now(),
    measurement_type=BiometricType.WEIGHT,
    data={"weight": 220.5, "unit": "lbs", "body_fat": 25.2},
    metadata={"source": "smart_scale", "accuracy": "high"}
)
await twin.add_biometric_entry(weight_entry)

# Track milestone
await twin.track_milestone(
    category="weight_loss",
    title="First 10 lbs Lost",
    description="Lost 10 lbs in 4 weeks through morning workouts",
    impact_metrics={"weight_change": -10, "energy_improvement": 3}
)

# Get insights
insights = await twin.get_pattern_insights("weight_loss", timeframe_days=30)
```

## Database Schema

### Core Tables
- **user_profiles** - User metadata and preferences
- **biometric_timeline** - All measurements over time
- **milestones** - Significant achievements

### Advanced Tables (Future phases)
- **memory_episodes** - Conversation history
- **discovered_patterns** - AI-identified patterns
- **intervention_outcomes** - Scientific method tracking

## Architecture Benefits

### 🔒 Data Persistence
- **Years of data** without loss
- **Efficient retrieval** with proper indexing
- **Scalable storage** for growing datasets

### 🎯 Personalization
- **User-specific patterns** discovered over time
- **Preference evolution** tracking
- **Intervention effectiveness** measurement

### 📈 Compound Knowledge
- **More data = greater value**
- **Pattern confidence** increases with data volume
- **Scientific validation** of interventions

## Development Notes

### Type Safety
- Full type hints throughout
- Async/await for all database operations
- Comprehensive error handling

### Testing
- SQLite version for rapid prototyping
- PostgreSQL version for production
- Comprehensive demo scripts

### Integration
- Designed to integrate with existing memory modules
- Foundation for temporal RAG system
- Supports federated specialist architecture

## Next Steps
1. **Temporal RAG** implementation
2. **Federated specialists** integration
3. **Compound memory engine** for hypothesis testing
4. **Visual progress tracking** (MIRAGE protocol)

## Memory is Everything
This system embodies AUREN's core principle: **every interaction makes the system smarter**. A DEXA scan today is valuable. Ten DEXA scans over 6 months reveal your transformation story.
