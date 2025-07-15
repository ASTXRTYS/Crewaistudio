"""
Test script for Cognitive Twin Profile.
Demonstrates the core functionality of AUREN's long-term memory system.
"""

import asyncio
import asyncpg
import os
from datetime import datetime, timedelta
from cognitive_twin_profile import CognitiveTwinProfile, BiometricEntry, BiometricType, Milestone

async def create_test_database():
    """Create a test database for demonstration purposes."""
    database_url = os.getenv("DATABASE_URL", "postgresql://localhost/auren")
    
    # Setup database
    from setup_database import setup_database, create_test_user
    await setup_database(database_url)
    await create_test_user(database_url)
    
    return database_url

async def demonstrate_cognitive_twin():
    """Demonstrate the complete Cognitive Twin Profile functionality."""
    print("🧠 AUREN Cognitive Twin Profile Demo")
    print("=" * 50)
    
    # Setup database
    database_url = await create_test_database()
    
    # Create connection pool
    pool = await asyncpg.create_pool(database_url)
    
    try:
        # Create Cognitive Twin for test user
        user_id = "test_user_astxryts"
        twin = CognitiveTwinProfile(user_id, pool)
        
        print(f"\n1. Initializing profile for user: {user_id}")
        await twin.initialize()
        summary = twin.get_summary()
        print(f"   Profile created: {summary['profile_created']}")
        
        # Add biometric entries
        print("\n2. Adding biometric entries...")
        
        # Weight tracking
        weight_entry = BiometricEntry(
            user_id=user_id,
            timestamp=datetime.now() - timedelta(days=30),
            measurement_type=BiometricType.WEIGHT,
            data={"weight": 226.0, "unit": "lbs", "body_fat": 28.5},
            metadata={"source": "smart_scale", "accuracy": "high"}
        )
        await twin.add_biometric_entry(weight_entry)
        print("   ✅ Added initial weight: 226 lbs")
        
        weight_entry2 = BiometricEntry(
            user_id=user_id,
            timestamp=datetime.now() - timedelta(days=7),
            measurement_type=BiometricType.WEIGHT,
            data={"weight": 218.5, "unit": "lbs", "body_fat": 26.8},
            metadata={"source": "smart_scale", "accuracy": "high"}
        )
        await twin.add_biometric_entry(weight_entry2)
        print("   ✅ Added recent weight: 218.5 lbs")
        
        # Energy tracking
        energy_entry = BiometricEntry(
            user_id=user_id,
            timestamp=datetime.now() - timedelta(days=1),
            measurement_type=BiometricType.ENERGY,
            data={"level": 8, "scale": "1-10", "time_of_day": "morning"},
            metadata={"context": "after_workout", "sleep_hours": 7.5}
        )
        await twin.add_biometric_entry(energy_entry)
        print("   ✅ Added energy level: 8/10")
        
        # Sleep tracking
        sleep_entry = BiometricEntry(
            user_id=user_id,
            timestamp=datetime.now() - timedelta(days=1),
            measurement_type=BiometricType.SLEEP,
            data={"hours": 7.5, "quality": "good", "deep_sleep": 2.1},
            metadata={"bedtime": "22:30", "waketime": "06:00"}
        )
        await twin.add_biometric_entry(sleep_entry)
        print("   ✅ Added sleep data: 7.5 hours")
        
        # Record milestone
        print("\n3. Recording milestone...")
        await twin.track_milestone(
            category="weight_loss",
            title="First 7.5 lbs Lost",
            description="Successfully lost 7.5 lbs in 3 weeks through consistent morning workouts and carb cycling",
            impact_metrics={
                "weight_change": -7.5,
                "body_fat_change": -1.7,
                "energy_improvement": 2.5,
                "confidence_boost": 15
            },
            tags=["weight_loss", "consistency", "morning_workouts", "carb_cycling"]
        )
        print("   ✅ Recorded milestone: First 7.5 lbs Lost")
        
        # Track preference evolution
        print("\n4. Tracking preference evolution...")
        await twin.track_preference_evolution(
            preference_type="workout_timing",
            preference_data={
                "preferred_time": "morning",
                "reason": "higher energy and consistency",
                "effectiveness": 9
            }
        )
        print("   ✅ Tracked workout timing preference")
        
        await twin.track_preference_evolution(
            preference_type="nutrition_style",
            preference_data={
                "current_approach": "carb_cycling",
                "previous_approaches": ["keto", "intermittent_fasting"],
                "effectiveness": 8.5,
                "notes": "better energy and sustainable"
            }
        )
        print("   ✅ Tracked nutrition style preference")
        
        # Get pattern insights
        print("\n5. Analyzing patterns...")
        
        weight_insights = await twin.get_pattern_insights(
            pattern_type="weight_loss",
            timeframe_days=30
        )
        print(f"   📊 Weight loss insights:")
        for pattern in weight_insights["patterns_found"]:
            print(f"      - {pattern['description']} (confidence: {pattern['confidence']})")
        
        energy_insights = await twin.get_pattern_insights(
            pattern_type="energy_optimization",
            timeframe_days=7
        )
        print(f"   ⚡ Energy insights:")
        for pattern in energy_insights["patterns_found"]:
            print(f"      - {pattern['description']} (confidence: {pattern['confidence']})")
        
        # Final summary
        print("\n6. Final profile summary:")
        final_summary = twin.get_summary()
        print(f"   User ID: {final_summary['user_id']}")
        print(f"   Profile created: {final_summary['profile_created']}")
        print(f"   Total milestones: {final_summary['total_milestones']}")
        print(f"   Latest biometrics: {len(final_summary['latest_biometrics'])} entries")
        print(f"   Preference categories: {final_summary['preference_categories']}")
        
        # Demonstrate history retrieval
        print("\n7. Retrieving biometric history...")
        weight_history = await twin.get_biometric_history(
            measurement_type=BiometricType.WEIGHT,
            days_back=30
        )
        print(f"   Found {len(weight_history)} weight entries")
        for entry in weight_history:
            date = entry['timestamp'].strftime('%Y-%m-%d') if hasattr(entry['timestamp'], 'strftime') else entry['timestamp'][:10]
            weight = entry['data'].get('weight', 'N/A')
            print(f"   - {date}: {weight} lbs")
        
        print("\n✅ Demo complete! AUREN now knows this user's optimization journey.")
        
    finally:
        await pool.close()

if __name__ == "__main__":
    asyncio.run(demonstrate_cognitive_twin())
