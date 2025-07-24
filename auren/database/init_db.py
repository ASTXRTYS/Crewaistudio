"""
Database Initialization Script
Sets up PostgreSQL schema for AUREN Cognitive Twin
"""

import asyncio
import logging
from pathlib import Path

from data_layer.connection import AsyncPostgresManager
from data_layer.event_store import EventStore
from data_layer.memory_backend import PostgreSQLMemoryBackend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_database(dsn: str = "postgresql://localhost:5432/auren") -> None:
    """
    Initialize the complete AUREN database schema
    
    Args:
        dsn: PostgreSQL connection string
    """
    logger.info("Initializing AUREN database...")
    
    try:
        # Initialize connection pool
        await AsyncPostgresManager.initialize(dsn)
        
        # Initialize event store
        event_store = EventStore()
        await event_store.initialize()
        logger.info("✅ Event store initialized")
        
        # Initialize memory backend
        memory_backend = PostgreSQLMemoryBackend(event_store)
        await memory_backend.initialize()
        logger.info("✅ Memory backend initialized")
        
        # Verify health
        health = await AsyncPostgresManager.health_check()
        if health["status"] == "healthy":
            logger.info("✅ Database health check passed")
        else:
            logger.error(f"❌ Database health check failed: {health}")
            return False
        
        # Test basic operations
        await _test_basic_operations(event_store, memory_backend)
        
        logger.info("🎉 AUREN database initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False
    finally:
        await AsyncPostgresManager.close()

async def _test_basic_operations(event_store: EventStore, memory_backend: PostgreSQLMemoryBackend) -> None:
    """Test basic database operations"""
    logger.info("Testing basic operations...")
    
    # Test event store
    test_stream = "test_user_123"
    event = await event_store.append_event(
        stream_id=test_stream,
        event_type=EventStore.EventType.MEMORY_CREATED,
        payload={"test": "data"}
    )
    logger.info(f"✅ Event stored: {event.event_id}")
    
    # Test memory backend
    memory_id = await memory_backend.store_memory(
        agent_id="test_agent",
        memory_type=memory_backend.MemoryType.FACT,
        content={"fact": "test_fact"},
        user_id=test_stream,
        confidence=0.9
    )
    logger.info(f"✅ Memory stored: {memory_id}")
    
    # Test retrieval
    memories = await memory_backend.retrieve_memories(
        agent_id="test_agent",
        user_id=test_stream,
        limit=5
    )
    logger.info(f"✅ Retrieved {len(memories)} memories")
    
    # Test search
    search_results = await memory_backend.search_memories(
        agent_id="test_agent",
        query="test",
        user_id=test_stream,
        limit=5
    )
    logger.info(f"✅ Found {len(search_results)} search results")

async def reset_database(dsn: str = "postgresql://localhost:5432/auren") -> None:
    """
    Reset the database (drop and recreate tables)
    
    Args:
        dsn: PostgreSQL connection string
    """
    logger.warning("Resetting database - this will delete all data!")
    
    try:
        await AsyncPostgresManager.initialize(dsn)
        
        async with AsyncPostgresManager.connection() as conn:
            # Drop existing tables
            await conn.execute("""
                DROP TABLE IF EXISTS agent_memories CASCADE;
                DROP TABLE IF EXISTS conversation_memories CASCADE;
                DROP TABLE IF EXISTS user_profiles CASCADE;
                DROP TABLE IF EXISTS specialist_knowledge CASCADE;
                DROP TABLE IF EXISTS events CASCADE;
            """)
            logger.info("✅ Existing tables dropped")
        
        # Reinitialize
        await initialize_database(dsn)
        
    except Exception as e:
        logger.error(f"❌ Database reset failed: {e}")
    finally:
        await AsyncPostgresManager.close()

async def verify_installation(dsn: str = "postgresql://localhost:5432/auren") -> bool:
    """
    Verify the database installation
    
    Args:
        dsn: PostgreSQL connection string
        
    Returns:
        bool: True if installation is valid
    """
    logger.info("Verifying database installation...")
    
    try:
        await AsyncPostgresManager.initialize(dsn)
        
        # Check if tables exist
        async with AsyncPostgresManager.connection() as conn:
            tables = await conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename IN ('events', 'agent_memories', 'conversation_memories', 
                                 'user_profiles', 'specialist_knowledge')
            """)
            
            expected_tables = 5
            actual_tables = len(tables)
            
            if actual_tables == expected_tables:
                logger.info(f"✅ All {expected_tables} tables present")
                
                # Test basic functionality
                event_store = EventStore()
                memory_backend = PostgreSQLMemoryBackend(event_store)
                
                # Test memory storage
                memory_id = await memory_backend.store_memory(
                    agent_id="verification_test",
                    memory_type=memory_backend.MemoryType.FACT,
                    content={"test": "verification"},
                    user_id="test_user",
                    confidence=1.0
                )
                
                # Test retrieval
                memories = await memory_backend.retrieve_memories(
                    agent_id="verification_test",
                    user_id="test_user",
                    limit=1
                )
                
                if len(memories) > 0:
                    logger.info("✅ Memory storage and retrieval working")
                    return True
                else:
                    logger.error("❌ Memory retrieval failed")
                    return False
            else:
                logger.error(f"❌ Expected {expected_tables} tables, found {actual_tables}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Installation verification failed: {e}")
        return False
    finally:
        await AsyncPostgresManager.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AUREN Database Management")
    parser.add_argument("--dsn", default="postgresql://localhost:5432/auren",
                        help="PostgreSQL connection string")
    parser.add_argument("--reset", action="store_true",
                        help="Reset database (drops all tables)")
    parser.add_argument("--verify", action="store_true",
                        help="Verify installation")
    
    args = parser.parse_args()
    
    if args.reset:
        asyncio.run(reset_database(args.dsn))
    elif args.verify:
        success = asyncio.run(verify_installation(args.dsn))
        exit(0 if success else 1)
    else:
        asyncio.run(initialize_database(args.dsn))
