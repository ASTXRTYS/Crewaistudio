"""
Async PostgreSQL Connection Manager
Provides robust connection pooling with health monitoring
"""

import asyncio
import asyncpg
from typing import Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class AsyncPostgresManager:
    """
    Singleton manager for PostgreSQL connections with automatic retry logic.
    
    Features:
    - Connection pooling (10-50 connections)
    - Health monitoring
    - Automatic retry with exponential backoff
    - Singleton pattern (one pool per application)
    """
    
    _instance: Optional['AsyncPostgresManager'] = None
    _pool: Optional[asyncpg.Pool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def initialize(cls, dsn: str, min_size: int = 10, max_size: int = 50) -> None:
        """Initialize the connection pool."""
        if cls._pool is None:
            try:
                cls._pool = await asyncpg.create_pool(
                    dsn=dsn,
                    min_size=min_size,
                    max_size=max_size,
                    command_timeout=30,
                    server_settings={
                        'application_name': 'auren_cognitive_twin',
                        'jit': 'off'  # Disable JIT for better performance
                    }
                )
                logger.info(f"PostgreSQL connection pool initialized: {min_size}-{max_size} connections")
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL pool: {e}")
                raise
    
    @classmethod
    async def get_connection(cls) -> asyncpg.Connection:
        """Get a connection from the pool."""
        if cls._pool is None:
            raise RuntimeError("PostgreSQL pool not initialized. Call initialize() first.")
        return await cls._pool.acquire()
    
    @classmethod
    async def release_connection(cls, connection: asyncpg.Connection) -> None:
        """Release a connection back to the pool."""
        if cls._pool:
            await cls._pool.release(connection)
    
    @classmethod
    @asynccontextmanager
    async def connection(cls):
        """Context manager for database connections."""
        conn = await cls.get_connection()
        try:
            yield conn
        finally:
            await cls.release_connection(conn)
    
    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """Check database health."""
        if cls._pool is None:
            return {"status": "uninitialized", "error": "Pool not initialized"}
        
        try:
            async with cls.connection() as conn:
                # Test basic connectivity
                result = await conn.fetchval("SELECT 1")
                if result != 1:
                    return {"status": "unhealthy", "error": "Basic query failed"}
                
                # Check connection pool stats
                pool_stats = {
                    "size": cls._pool.get_size(),
                    "idle": cls._pool.get_idle_size(),
                    "acquired": cls._pool.get_size() - cls._pool.get_idle_size()
                }
                
                return {
                    "status": "healthy",
                    "pool_stats": pool_stats,
                    "database": "auren"
                }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    @classmethod
    async def close(cls) -> None:
        """Close the connection pool."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("PostgreSQL connection pool closed")
    
    @classmethod
    async def execute_with_retry(cls, query: str, *args, max_retries: int = 3) -> Any:
        """Execute query with automatic retry on transient failures."""
        for attempt in range(max_retries):
            try:
                async with cls.connection() as conn:
                    return await conn.execute(query, *args)
            except asyncpg.exceptions.DeadlockDetectedError as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 0.1 * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Deadlock detected, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
            except asyncpg.exceptions.UniqueViolationError as e:
                # Don't retry unique violations - they're permanent
                raise
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Query failed, retrying: {e}")
                await asyncio.sleep(0.1)
