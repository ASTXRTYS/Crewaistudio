"""
Database setup script for AUREN Cognitive Twin Profile.
Creates PostgreSQL schema for all 4 phases to avoid future migrations.
"""

import asyncio
import asyncpg
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def setup_database(database_url: str = None):
    """
    Create the complete PostgreSQL schema for AUREN's Cognitive Twin Profile.
    This includes all 4 phases to prevent future migrations.
    """
    if database_url is None:
        database_url = os.getenv("DATABASE_URL", "postgresql://localhost/auren")
    
    conn = await asyncpg.connect(database_url)
    
    try:
        # Enable UUID extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        
        # Phase 1: Core Profile Tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) UNIQUE NOT NULL,
                profile_data JSONB NOT NULL DEFAULT '{}',
                preference_evolution JSONB NOT NULL DEFAULT '{}',
                optimization_history JSONB NOT NULL DEFAULT '[]',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_profiles_updated_at ON user_profiles(updated_at);
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS biometric_timeline (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                measurement_type VARCHAR(50) NOT NULL,
                data JSONB NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_biometric_user_id ON biometric_timeline(user_id);
            CREATE INDEX IF NOT EXISTS idx_biometric_user_type_time ON biometric_timeline(user_id, measurement_type, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_biometric_timestamp ON biometric_timeline(timestamp DESC);
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS milestones (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                category VARCHAR(100) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                impact_metrics JSONB NOT NULL,
                tags TEXT[] DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_milestones_user_id ON milestones(user_id);
            CREATE INDEX IF NOT EXISTS idx_milestones_user_category ON milestones(user_id, category);
            CREATE INDEX IF NOT EXISTS idx_milestones_timestamp ON milestones(timestamp DESC);
        """)
        
        # Phase 2: Enhanced Memory Tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_episodes (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                session_id VARCHAR(255),
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                content_type VARCHAR(50),
                content JSONB NOT NULL,
                metadata JSONB DEFAULT '{}',
                embedding VECTOR(1536),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_memory_episodes_user_id ON memory_episodes(user_id);
            CREATE INDEX IF NOT EXISTS idx_memory_episodes_session ON memory_episodes(user_id, session_id);
            CREATE INDEX IF NOT EXISTS idx_memory_episodes_timestamp ON memory_episodes(timestamp DESC);
        """)
        
        # Phase 3: Pattern Recognition Tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS discovered_patterns (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                pattern_type VARCHAR(100) NOT NULL,
                pattern_data JSONB NOT NULL,
                confidence_score FLOAT NOT NULL,
                timeframe_start DATE NOT NULL,
                timeframe_end DATE NOT NULL,
                validation_status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_patterns_user_type ON discovered_patterns(user_id, pattern_type);
            CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON discovered_patterns(confidence_score DESC);
        """)
        
        # Phase 4: Advanced Analytics
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS intervention_outcomes (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                intervention_type VARCHAR(100) NOT NULL,
                intervention_data JSONB NOT NULL,
                outcome_metrics JSONB NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                success_score FLOAT,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_interventions_user_type ON intervention_outcomes(user_id, intervention_type);
            CREATE INDEX IF NOT EXISTS idx_interventions_date ON intervention_outcomes(start_date DESC);
        """)
        
        # Create update trigger for user_profiles
        await conn.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
            
            DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
            CREATE TRIGGER update_user_profiles_updated_at
                BEFORE UPDATE ON user_profiles
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)
        
        logger.info("Database schema created successfully for all 4 phases")
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        raise
    finally:
        await conn.close()

async def create_test_user(database_url: str = None):
    """Create a test user for development purposes."""
    if database_url is None:
        database_url = os.getenv("DATABASE_URL", "postgresql://localhost/auren")
    
    conn = await asyncpg.connect(database_url)
    
    try:
        test_user_id = "test_user_astxryts"
        
        # Check if test user exists
        exists = await conn.fetchval(
            "SELECT 1 FROM user_profiles WHERE user_id = $1",
            test_user_id
        )
        
        if not exists:
            await conn.execute("""
                INSERT INTO user_profiles (user_id, profile_data)
                VALUES ($1, $2)
            """, test_user_id, {
                "created_at": datetime.now().isoformat(),
                "initial_state": "test_user",
                "test_data": True
            })
            
            logger.info(f"Created test user: {test_user_id}")
        else:
            logger.info(f"Test user already exists: {test_user_id}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup AUREN database")
    parser.add_argument("--database-url", help="PostgreSQL connection string")
    parser.add_argument("--create-test-user", action="store_true", help="Create test user")
    
    args = parser.parse_args()
    
    async def main():
        await setup_database(args.database_url)
        if args.create_test_user:
            await create_test_user(args.database_url)
        print("✅ Database setup complete!")
    
    asyncio.run(main())
