#!/usr/bin/env python3
"""
Setup script for AUREN Cognitive Twin Profile.
This script helps users set up the database and test the integration.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.database import db
from core.config import get_config, validate_environment

async def setup_database():
    """Set up the database schema for Cognitive Twin."""
    print("🧠 Setting up AUREN Cognitive Twin Database...")
    
    try:
        # Validate environment
        print("1. Checking environment configuration...")
        validate_environment()
        config = get_config()
        print(f"   ✅ Database URL: {config['database_url'][:50]}...")
        
        # Initialize database
        print("2. Initializing database connection...")
        await db.initialize()
        print("   ✅ Database connected")
        
        # Create tables
        print("3. Creating database schema...")
        async with db.pool.acquire() as conn:
            # Create user_profiles table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id VARCHAR(255) PRIMARY KEY,
                    profile_data JSONB NOT NULL DEFAULT '{}',
                    preference_evolution JSONB NOT NULL DEFAULT '{}',
                    optimization_history JSONB NOT NULL DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create biometric_timeline table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS biometric_timeline (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    measurement_type VARCHAR(50) NOT NULL,
                    data JSONB NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
                )
            """)
            
            # Create milestones table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS milestones (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    impact_metrics JSONB NOT NULL,
                    tags TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
                )
            """)
            
            # Create indexes for performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_biometric_user_type_time 
                ON biometric_timeline(user_id, measurement_type, timestamp DESC)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_milestones_user_time 
                ON milestones(user_id, timestamp DESC)
            """)
            
        print("   ✅ Database schema created")
        
        # Test the setup
        print("4. Testing Cognitive Twin integration...")
        from services.cognitive_twin_service import CognitiveTwinService
        
        service = CognitiveTwinService(db.pool)
        
        # Test basic functionality
        test_user = "setup_test_user"
        
        # Track test data
        result = await service.track_weight(test_user, 200.0, "lbs")
        print(f"   ✅ Weight tracking: {result.message}")
        
        result = await service.track_energy(test_user, 8, "morning")
        print(f"   ✅ Energy tracking: {result['message']}")
        
        # Get insights
        insights = await service.get_weight_insights(test_user)
        print(f"   ✅ Insights generation: {insights.message}")
        
        # Clean up test data
        async with db.pool.acquire() as conn:
            await conn.execute("DELETE FROM biometric_timeline WHERE user_id = $1", test_user)
            await conn.execute("DELETE FROM user_profiles WHERE user_id = $1", test_user)
        
        print("\n🎉 Setup complete! AUREN Cognitive Twin is ready to use.")
        print("\nNext steps:")
        print("1. Copy .env.template to .env and configure your database")
        print("2. Run: python demo_cognitive_service.py")
        print("3. Run: python src/agents/auren_with_cognitive.py")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running")
        print("2. Check DATABASE_URL in .env file")
        print("3. Verify database credentials")
        
    finally:
        await db.close()

def main():
    """Main setup function."""
    asyncio.run(setup_database())

if __name__ == "__main__":
    main()
