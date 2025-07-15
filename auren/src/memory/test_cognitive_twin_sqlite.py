"""
SQLite test script for Cognitive Twin Profile.
Demonstrates the core functionality without requiring PostgreSQL.
"""

import asyncio
import aiosqlite
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cognitive_twin_profile import BiometricEntry, BiometricType, Milestone

class SQLiteCognitiveTwin:
    """
    SQLite version of Cognitive Twin for testing without PostgreSQL.
    This demonstrates the same functionality using SQLite.
    """
    
    def __init__(self, user_id: str, db_path: str = "auren_test.db"):
        self.user_id = user_id
        self.db_path = db_path
        self._cache = {}
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize or load existing profile from SQLite database."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create tables if they don't exist
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data TEXT NOT NULL,
                    preference_evolution TEXT NOT NULL DEFAULT '{}',
                    optimization_history TEXT NOT NULL DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS biometric_timeline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    measurement_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS milestones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    impact_metrics TEXT NOT NULL,
                    tags TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
            
            # Check if user exists
            cursor = await db.execute(
                "SELECT * FROM user_profiles WHERE user_id = ?",
                (self.user_id,)
            )
            user_data = await cursor.fetchone()
            
            if not user_data:
                # Create new profile
                await db.execute("""
                    INSERT INTO user_profiles (user_id, profile_data)
                    VALUES (?, ?)
                """, (self.user_id, json.dumps({
                    "created_at": datetime.now().isoformat(),
                    "initial_state": "new_user"
                })))
                self._cache = {"profile_data": {"initial_state": "new_user"}}
            else:
                # Load existing profile
                self._cache = {
                    "profile_data": json.loads(user_data[1]),
                    "preferences": json.loads(user_data[2]),
                    "optimization_history": json.loads(user_data[3])
                }
        
        self._initialized = True
        print(f"✅ Initialized SQLite CognitiveTwinProfile for user: {self.user_id}")
    
    async def add_biometric_entry(self, entry: BiometricEntry) -> None:
        """Add a biometric measurement to the timeline."""
        if not self._initialized:
            await self.initialize()
            
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO biometric_timeline 
                (user_id, timestamp, measurement_type, data, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (entry.user_id, entry.timestamp, entry.measurement_type.value,
                  json.dumps(entry.data), json.dumps(entry.metadata)))
            await db.commit()
        
        # Update cache
        if 'latest_biometrics' not in self._cache:
            self._cache['latest_biometrics'] = {}
        self._cache['latest_biometrics'][entry.measurement_type.value] = entry.to_dict()
        
    async def get_biometric_history(
        self,
        measurement_type: Optional[BiometricType] = None,
        days_back: int = 30,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve biometric history with intelligent filtering."""
        query = """
            SELECT * FROM biometric_timeline 
            WHERE user_id = ? 
            AND timestamp >= ?
        """
        params = [self.user_id, datetime.now() - timedelta(days=days_back)]
        
        if measurement_type:
            query += " AND measurement_type = ?"
            params.append(measurement_type.value)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
        return [
            {
                "id": row[0],
                "user_id": row[1],
                "timestamp": row[2],
                "measurement_type": row[3],
                "data": json.loads(row[4]),
                "metadata": json.loads(row[5]),
                "created_at": row[6]
            }
            for row in rows
        ]
    
    async def track_milestone(
        self,
        category: str,
        title: str,
        description: str,
        impact_metrics: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> None:
        """Record significant achievements or events."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO milestones 
                (user_id, timestamp, category, title, description, impact_metrics, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.user_id, datetime.now(), category, title, description,
                  json.dumps(impact_metrics), json.dumps(tags or [])))
            await db.commit()
        
        # Update cache
        if 'optimization_history' not in self._cache:
            self._cache['optimization_history'] = []
        
        self._cache['optimization_history'].append({
            "timestamp": datetime.now().isoformat(),
            "type": "milestone",
            "category": category,
            "title": title,
            "impact": impact_metrics
        })
    
    async def track_preference_evolution(
        self,
        preference_type: str,
        preference_data: Dict[str, Any]
    ) -> None:
        """Track how user preferences evolve over time."""
        if 'preferences' not in self._cache:
            self._cache['preferences'] = {}
        
        if preference_type not in self._cache['preferences']:
            self._cache['preferences'][preference_type] = []
        
        self._cache['preferences'][preference_type].append({
            "timestamp": datetime.now().isoformat(),
            "data": preference_data
        })
        
        # Keep only last 10 entries
        self._cache['preferences'][preference_type] = \
            self._cache['preferences'][preference_type][-10:]
    
    async def get_pattern_insights(
        self,
        pattern_type: str,
        timeframe_days: int = 90
    ) -> Dict[str, Any]:
        """Analyze patterns in user data over extended timeframes."""
        start_date = datetime.now() - timedelta(days=timeframe_days)
        
        insights = {
            "pattern_type": pattern_type,
            "timeframe_days": timeframe_days,
            "patterns_found": []
        }
        
        if pattern_type == "weight_loss":
            weight_history = await self.get_biometric_history(
                measurement_type=BiometricType.WEIGHT,
                days_back=timeframe_days
            )
            
            if len(weight_history) >= 2:
                start_weight = weight_history[-1]['data'].get('weight')
                current_weight = weight_history[0]['data'].get('weight')
                
                if start_weight and current_weight:
                    total_loss = start_weight - current_weight
                    rate_per_week = (total_loss / timeframe_days) * 7
                    
                    insights["patterns_found"].append({
                        "pattern": "weight_loss_rate",
                        "description": f"Average weight loss of {rate_per_week:.2f} lbs/week",
                        "confidence": 0.8 if len(weight_history) > 10 else 0.5
                    })
        
        elif pattern_type == "energy_optimization":
            energy_history = await self.get_biometric_history(
                measurement_type=BiometricType.ENERGY,
                days_back=timeframe_days
            )
            
            morning_energy = [e for e in energy_history 
                            if datetime.fromisoformat(e['timestamp']).hour < 12]
            
            if morning_energy:
                avg_morning = sum(e['data'].get('level', 5) for e in morning_energy) / len(morning_energy)
                insights["patterns_found"].append({
                    "pattern": "morning_energy",
                    "description": f"Average morning energy: {avg_morning:.1f}/10",
                    "confidence": min(0.9, len(morning_energy) / 30)
                })
        
        return insights
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the user's profile."""
        return {
            "user_id": self.user_id,
            "profile_created": self._cache.get("profile_data", {}).get("created_at"),
            "total_milestones": len(self._cache.get("optimization_history", [])),
            "latest_biometrics": self._cache.get("latest_biometrics", {}),
            "preference_categories": list(self._cache.get("preferences", {}).keys())
        }

async def demonstrate_sqlite_cognitive_twin():
    """Demonstrate the complete Cognitive Twin functionality using SQLite."""
    print("🧠 AUREN Cognitive Twin Profile Demo (SQLite)")
    print("=" * 55)
    
    # Install aiosqlite if needed
    try:
        import aiosqlite
    except ImportError:
        print("Installing aiosqlite...")
        import subprocess
        subprocess.run(["python", "-m", "pip", "install", "aiosqlite"])
        import aiosqlite
    
    # Create Cognitive Twin for test user
    user_id = "test_user_astxryts"
    twin = SQLiteCognitiveTwin(user_id)
    
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
        date = entry['timestamp'][:10] if isinstance(entry['timestamp'], str) else str(entry['timestamp'])[:10]
        weight = entry['data'].get('weight', 'N/A')
        print(f"   - {date}: {weight} lbs")
    
    print("\n✅ Demo complete! AUREN now knows this user's optimization journey.")
    print("   Database file created: auren_test.db")

if __name__ == "__main__":
    asyncio.run(demonstrate_sqlite_cognitive_twin())
