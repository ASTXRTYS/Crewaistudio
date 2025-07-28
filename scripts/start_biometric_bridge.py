#!/usr/bin/env python3
"""
AUREN Biometric Bridge Launch Script
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
import redis
from kafka import KafkaProducer

from auren.biometric import BiometricKafkaLangGraphBridge, load_biometric_config
from auren.agents.neuros_graph import create_neuros_graph


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_postgres_pool():
    """Create PostgreSQL connection pool"""
    postgres_url = os.getenv(
        "POSTGRES_URL", 
        "postgresql://auren_user:auren_password_2024@localhost:5432/auren_db"
    )
    
    logger.info(f"Connecting to PostgreSQL...")
    pool = await asyncpg.create_pool(
        postgres_url,
        min_size=10,
        max_size=30,
        command_timeout=60
    )
    
    # Test connection
    async with pool.acquire() as conn:
        version = await conn.fetchval("SELECT version()")
        logger.info(f"PostgreSQL connected: {version}")
    
    return pool


def create_redis_client():
    """Create Redis client"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    logger.info(f"Connecting to Redis...")
    client = redis.from_url(redis_url, decode_responses=True)
    
    # Test connection
    client.ping()
    logger.info("Redis connected")
    
    return client


def create_kafka_config():
    """Create Kafka configuration"""
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    return {
        "bootstrap_servers": bootstrap_servers
    }


async def main():
    """Main entry point"""
    logger.info("Starting AUREN Biometric Bridge...")
    
    try:
        # Create connections
        postgres_pool = await create_postgres_pool()
        redis_client = create_redis_client()
        kafka_config = create_kafka_config()
        
        # Create NEUROS graph
        logger.info("Creating NEUROS cognitive graph...")
        neuros_graph = create_neuros_graph()
        
        # Load configuration
        config_path = os.getenv("BIOMETRIC_CONFIG", "config/biometric_thresholds.yaml")
        logger.info(f"Loading configuration from {config_path}")
        
        # Create bridge
        bridge = BiometricKafkaLangGraphBridge(
            graph=neuros_graph,
            kafka_config=kafka_config,
            postgres_pool=postgres_pool,
            redis_client=redis_client,
            max_concurrent_events=int(os.getenv("MAX_CONCURRENT_EVENTS", "50")),
            config_path=config_path
        )
        
        logger.info("Biometric Bridge initialized successfully")
        logger.info(f"Configuration: {bridge.thresholds}")
        
        # Start consuming
        logger.info("Starting Kafka consumer...")
        await bridge.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
        if 'bridge' in locals():
            await bridge.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        if 'postgres_pool' in locals():
            await postgres_pool.close()
        if 'redis_client' in locals():
            redis_client.close()
        
        logger.info("Biometric Bridge stopped")


if __name__ == "__main__":
    asyncio.run(main()) 