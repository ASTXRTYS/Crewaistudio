#!/usr/bin/env python3
"""
NEUROS Migration Script: v3.1 → Advanced Reasoning (Phases 5-8)
==============================================================
This script migrates the current NEUROS implementation to the new
LangGraph-based architecture with advanced reasoning capabilities.

Prerequisites:
- PostgreSQL with pgvector extension
- Redis running
- Docker Compose environment
- Backup of current state

Usage:
    python migrate_neuros_advanced.py --config config/neuros_config.json [--dry-run]
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
import yaml
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NEUROSMigration:
    """Handles migration from current NEUROS to advanced LangGraph version."""
    
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
        
    async def backup_current_state(self):
        """Backup current NEUROS state before migration."""
        logger.info("Creating backup of current NEUROS state...")
        
        if self.dry_run:
            logger.info("[DRY RUN] Would create backup at: backups/neuros_pre_migration_{timestamp}.sql")
            return
            
        backup_path = Path("backups") / f"neuros_pre_migration_{self.migration_timestamp.strftime('%Y%m%d_%H%M%S')}.sql"
        backup_path.parent.mkdir(exist_ok=True)
        
        # Backup PostgreSQL data
        async with self.pg_pool.acquire() as conn:
            # Get all NEUROS-related tables
            tables = await conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename LIKE '%neuros%' OR tablename LIKE '%checkpoint%'
            """)
            
            with open(backup_path, 'w') as f:
                for table in tables:
                    logger.info(f"  Backing up table: {table['tablename']}")
                    
                    # Export table structure
                    structure = await conn.fetchval(f"""
                        SELECT pg_get_ddl('table', '{table['tablename']}')
                    """)
                    f.write(f"-- Table: {table['tablename']}\n")
                    f.write(f"{structure};\n\n")
                    
                    # Export table data
                    rows = await conn.fetch(f"SELECT * FROM {table['tablename']}")
                    if rows:
                        # Generate INSERT statements
                        for row in rows:
                            values = ', '.join([f"'{v}'" if v is not None else 'NULL' for v in row.values()])
                            f.write(f"INSERT INTO {table['tablename']} VALUES ({values});\n")
                        f.write("\n")
                        
        logger.info(f"✓ Backup created: {backup_path}")
        
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
                logger.error(f"Failed to install pgvector: {e}")
                logger.info("Please install pgvector manually: CREATE EXTENSION vector;")
                raise
                
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
                logger.info(f"  - {schema.split('(')[0].strip()}")
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
                    index_name = index.split('INDEX')[1].split('ON')[0].strip()
                    logger.info(f"  ✓ Created index: {index_name}")
                except Exception as e:
                    logger.error(f"  ✗ Failed to create index: {e}")
                    raise
                    
    async def migrate_existing_data(self):
        """Migrate existing conversation and state data."""
        logger.info("Migrating existing NEUROS data...")
        
        if self.dry_run:
            logger.info("[DRY RUN] Would migrate existing conversation history and checkpoints")
            return
            
        async with self.pg_pool.acquire() as conn:
            # Check for existing checkpoints
            checkpoint_count = await conn.fetchval("""
                SELECT COUNT(*) FROM checkpoints 
                WHERE thread_id LIKE 'neuros-%'
            """)
            
            if checkpoint_count > 0:
                logger.info(f"  Found {checkpoint_count} NEUROS conversation checkpoints")
                
                # Migrate checkpoints to narrative memories
                checkpoints = await conn.fetch("""
                    SELECT thread_id, checkpoint, metadata
                    FROM checkpoints
                    WHERE thread_id LIKE 'neuros-%'
                    ORDER BY thread_ts DESC
                """)
                
                migrated = 0
                for checkpoint in tqdm(checkpoints, desc="Migrating checkpoints"):
                    try:
                        # Extract user_id from thread_id
                        user_id = checkpoint['thread_id'].split('-')[1] if '-' in checkpoint['thread_id'] else 'unknown'
                        
                        # Parse checkpoint data
                        checkpoint_data = json.loads(checkpoint['checkpoint']) if isinstance(checkpoint['checkpoint'], str) else checkpoint['checkpoint']
                        
                        # Create narrative memory entry
                        await conn.execute("""
                            INSERT INTO narrative_memories 
                            (user_id, timestamp, memory_type, content, metadata, arc_phase)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT DO NOTHING
                        """,
                        user_id,
                        datetime.now(),  # Use current time as we don't have original
                        'migrated_checkpoint',
                        json.dumps(checkpoint_data.get('messages', [])),
                        checkpoint['metadata'] or {},
                        'baseline'  # Default arc phase
                        )
                        migrated += 1
                    except Exception as e:
                        logger.warning(f"  Failed to migrate checkpoint {checkpoint['thread_id']}: {e}")
                        
                logger.info(f"  ✓ Migrated {migrated}/{checkpoint_count} checkpoints")
                
    async def update_configuration(self):
        """Update configuration files for new architecture."""
        logger.info("Updating configuration files...")
        
        if self.dry_run:
            logger.info("[DRY RUN] Would update docker-compose.yml and neuros_config.json")
            return
            
        # Update neuros_config.json with new settings
        config_updates = {
            "neuros": {
                "version": "4.0-advanced",
                "architecture": "langgraph",
                "features": {
                    "weak_signal_detection": True,
                    "narrative_memory": True,
                    "identity_modeling": True,
                    "graceful_degradation": True
                },
                "memory": {
                    "backend": "postgresql_pgvector",
                    "conversation_window": 10,
                    "narrative_retention_days": 90,
                    "identity_tracking_days": 180
                },
                "personality": {
                    "curiosity_level": 0.8,
                    "empathy_baseline": 0.9,
                    "metaphor_frequency": 0.6,
                    "technical_translation": 0.95,
                    "coaching_intensity": 0.7
                }
            }
        }
        
        # Merge with existing config
        updated_config = {**self.config, **config_updates}
        
        # Save updated config
        config_path = Path("config/neuros_config.json")
        config_path.parent.mkdir(exist_ok=True)
        
        # Backup original
        if config_path.exists():
            backup_path = config_path.with_suffix(f".backup_{self.migration_timestamp.strftime('%Y%m%d_%H%M%S')}")
            config_path.rename(backup_path)
            logger.info(f"  ✓ Backed up original config to: {backup_path}")
            
        # Write new config
        with open(config_path, 'w') as f:
            json.dump(updated_config, f, indent=2)
        logger.info(f"  ✓ Updated configuration: {config_path}")
        
    async def verify_migration(self):
        """Verify migration completed successfully."""
        logger.info("Verifying migration...")
        
        checks = []
        
        async with self.pg_pool.acquire() as conn:
            # Check tables exist
            tables = ['narrative_memories', 'weak_signals', 'identity_markers', 'biometric_cache']
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
        """Execute the full migration."""
        try:
            logger.info(f"\n{'='*60}")
            logger.info("NEUROS Advanced Reasoning Migration")
            logger.info(f"{'='*60}")
            logger.info(f"Dry Run: {self.dry_run}")
            logger.info(f"Timestamp: {self.migration_timestamp}")
            logger.info("")
            
            # Initialize connections
            await self.initialize_connections()
            
            # Step 1: Backup
            await self.backup_current_state()
            
            # Step 2: Install pgvector
            await self.install_pgvector_extension()
            
            # Step 3: Create schema
            await self.create_advanced_schema()
            
            # Step 4: Migrate data
            await self.migrate_existing_data()
            
            # Step 5: Update configuration
            await self.update_configuration()
            
            # Step 6: Verify
            success = await self.verify_migration()
            
            if success and not self.dry_run:
                logger.info("\n🎉 NEUROS is now ready with advanced reasoning capabilities!")
                logger.info("\nNext steps:")
                logger.info("1. Restart NEUROS container with new configuration")
                logger.info("2. Test personality consistency with integration tests")
                logger.info("3. Monitor logs for any issues")
                logger.info("4. Once biometric pipeline is fixed, full capabilities will activate")
                
        except Exception as e:
            logger.error(f"\n❌ Migration failed: {e}")
            logger.error("Please check logs and restore from backup if needed")
            raise
        finally:
            # Cleanup connections
            if self.pg_pool:
                await self.pg_pool.close()
            if self.redis_client:
                await self.redis_client.close()

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate NEUROS to advanced reasoning architecture")
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
    migration = NEUROSMigration(config, dry_run=args.dry_run)
    await migration.run()

if __name__ == "__main__":
    asyncio.run(main())