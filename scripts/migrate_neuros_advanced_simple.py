#!/usr/bin/env python3
"""
NEUROS Migration Script (Simplified) - v3.1 → Advanced Reasoning
================================================================
A simplified version that focuses on essential schema creation.
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import asyncpg
from redis import asyncio as redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NEUROSMigrationSimple:
    """Simplified migration focusing on schema creation."""
    
    def __init__(self, config: Dict[str, Any], dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.migration_timestamp = datetime.now()
        
    async def initialize_connections(self):
        """Initialize database connections."""
        logger.info("Initializing database connections...")
        
        # PostgreSQL connection
        self.pg_pool = await asyncpg.create_pool(
            host=self.config["postgres"]["host"],
            port=self.config["postgres"]["port"],
            user=self.config["postgres"]["user"],
            password=self.config["postgres"]["password"],
            database=self.config["postgres"]["database"],
            min_size=5,
            max_size=10
        )
        
        # Redis connection
        self.redis_client = await redis.from_url(
            f"redis://{self.config['redis']['host']}:{self.config['redis']['port']}",
            decode_responses=True
        )
        
        logger.info("✓ Database connections established")
        
    async def install_pgvector_extension(self):
        """Install pgvector extension for narrative memory."""
        logger.info("Installing pgvector extension...")
        
        if self.dry_run:
            logger.info("[DRY RUN] Would install pgvector extension")
            return
            
        async with self.pg_pool.acquire() as conn:
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                logger.info("✓ pgvector extension installed")
            except Exception as e:
                logger.warning(f"pgvector extension may already exist or require manual installation: {e}")
                
    async def create_advanced_schema(self):
        """Create schema for advanced reasoning features."""
        logger.info("Creating advanced reasoning schema...")
        
        schemas = [
            # Narrative memory table
            """
            CREATE TABLE IF NOT EXISTS narrative_memories (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                memory_type VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                embedding vector(1536),
                metadata JSONB DEFAULT '{}',
                arc_phase VARCHAR(50),
                emotional_tone VARCHAR(50),
                turning_point BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Weak signals tracking
            """
            CREATE TABLE IF NOT EXISTS weak_signals (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                signal_type VARCHAR(100) NOT NULL,
                confidence FLOAT NOT NULL,
                supporting_metrics TEXT[],
                first_detected TIMESTAMP NOT NULL,
                last_updated TIMESTAMP NOT NULL,
                trend_velocity FLOAT,
                forecast_window INTERVAL,
                narrative_context TEXT,
                metadata JSONB DEFAULT '{}'
            )
            """,
            
            # Identity evolution tracking
            """
            CREATE TABLE IF NOT EXISTS identity_markers (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                marker_type VARCHAR(50) NOT NULL,
                current_archetype VARCHAR(50),
                archetype_scores JSONB NOT NULL,
                evidence JSONB DEFAULT '[]',
                strength FLOAT,
                metadata JSONB DEFAULT '{}'
            )
            """,
            
            # Biometric cache for fallback
            """
            CREATE TABLE IF NOT EXISTS biometric_cache (
                user_id VARCHAR(255) PRIMARY KEY,
                biometric_data JSONB NOT NULL,
                source VARCHAR(50) NOT NULL,
                recorded_at TIMESTAMP NOT NULL,
                reliability_score FLOAT DEFAULT 1.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Multi-agent readiness (for future)
            """
            CREATE TABLE IF NOT EXISTS agent_harmony_state (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                active_agents JSONB NOT NULL,
                conflicts JSONB DEFAULT '[]',
                harmony_score FLOAT DEFAULT 1.0,
                resolutions JSONB DEFAULT '[]'
            )
            """
        ]
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_narrative_user_time ON narrative_memories(user_id, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_narrative_embedding ON narrative_memories USING ivfflat (embedding vector_cosine_ops)",
            "CREATE INDEX IF NOT EXISTS idx_weak_signals_user ON weak_signals(user_id, last_updated DESC)",
            "CREATE INDEX IF NOT EXISTS idx_identity_user_time ON identity_markers(user_id, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_biometric_cache_user ON biometric_cache(user_id, updated_at DESC)"
        ]
        
        if self.dry_run:
            logger.info("[DRY RUN] Would create the following tables:")
            for schema in schemas:
                table_name = schema.split('EXISTS')[1].split('(')[0].strip()
                logger.info(f"  - {table_name}")
            return
            
        async with self.pg_pool.acquire() as conn:
            # Create tables
            for schema in schemas:
                try:
                    await conn.execute(schema)
                    table_name = schema.split('EXISTS')[1].split('(')[0].strip()
                    logger.info(f"  ✓ Created table: {table_name}")
                except Exception as e:
                    logger.error(f"  ✗ Failed to create table: {e}")
                    raise
                    
            # Create indexes
            for index in indexes:
                try:
                    await conn.execute(index)
                    index_name = index.split('IF NOT EXISTS')[1].split('ON')[0].strip()
                    logger.info(f"  ✓ Created index: {index_name}")
                except Exception as e:
                    logger.warning(f"  Index creation warning (may already exist): {e}")
                    
    async def verify_migration(self):
        """Verify migration completed successfully."""
        logger.info("Verifying migration...")
        
        checks = []
        
        async with self.pg_pool.acquire() as conn:
            # Check tables exist
            tables = ['narrative_memories', 'weak_signals', 'identity_markers', 'biometric_cache', 'agent_harmony_state']
            for table in tables:
                exists = await conn.fetchval(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """)
                checks.append((f"Table {table}", exists))
                
            # Check pgvector extension
            pgvector_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_extension WHERE extname = 'vector'
                )
            """)
            checks.append(("pgvector extension", pgvector_exists))
            
        # Check Redis connection
        try:
            await self.redis_client.ping()
            checks.append(("Redis connection", True))
        except:
            checks.append(("Redis connection", False))
            
        # Display results
        logger.info("\nMigration Verification Results:")
        all_passed = True
        for check, passed in checks:
            status = "✓" if passed else "✗"
            logger.info(f"  {status} {check}")
            if not passed:
                all_passed = False
                
        if all_passed:
            logger.info("\n✅ Migration completed successfully!")
        else:
            logger.error("\n❌ Migration incomplete - please check failed items")
            
        return all_passed
        
    async def run(self):
        """Execute the migration."""
        try:
            logger.info(f"\n{'='*60}")
            logger.info("NEUROS Advanced Reasoning Migration (Simplified)")
            logger.info(f"{'='*60}")
            logger.info(f"Dry Run: {self.dry_run}")
            logger.info(f"Timestamp: {self.migration_timestamp}")
            logger.info("")
            
            # Initialize connections
            await self.initialize_connections()
            
            # Step 1: Install pgvector
            await self.install_pgvector_extension()
            
            # Step 2: Create schema
            await self.create_advanced_schema()
            
            # Step 3: Verify
            success = await self.verify_migration()
            
            if success and not self.dry_run:
                logger.info("\n🎉 NEUROS is now ready with advanced reasoning capabilities!")
                logger.info("\nNext steps:")
                logger.info("1. Deploy the new NEUROS implementation")
                logger.info("2. Test personality consistency")
                logger.info("3. Monitor logs for any issues")
                
        except Exception as e:
            logger.error(f"\n❌ Migration failed: {e}")
            raise
        finally:
            # Cleanup connections
            if self.pg_pool:
                await self.pg_pool.close()
            if self.redis_client:
                await self.redis_client.close()

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate NEUROS to advanced reasoning architecture (simplified)")
    parser.add_argument("--config", required=True, help="Path to neuros_config.json")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without making changes")
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config) as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
        
    # Run migration
    migration = NEUROSMigrationSimple(config, dry_run=args.dry_run)
    await migration.run()

if __name__ == "__main__":
    asyncio.run(main()) 