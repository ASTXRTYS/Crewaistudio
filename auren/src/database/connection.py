"""
Database connection module for AUREN
Handles PostgreSQL connections with asyncpg for high-performance async operations
"""

import os
import asyncpg
from typing import Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Manages PostgreSQL connection pool for AUREN
    
    This class provides a singleton connection pool that's shared across
    the application. Using asyncpg for better performance compared to
    standard psycopg2, especially important for our real-time requirements.
    """
    
    _instance: Optional[asyncpg.Pool] = None
    _initialized: bool = False
    
    @classmethod
    async def initialize(cls, **kwargs) -> asyncpg.Pool:
        """
        Initialize the database connection pool
        
        This should be called once at application startup. Subsequent calls
        will return the existing pool unless force_reset is True.
        """
        if cls._instance is not None and cls._initialized:
            return cls._instance
        
        # Get connection parameters from environment or use defaults
        connection_params = {
            'host': kwargs.get('host', os.getenv('DB_HOST', 'localhost')),
            'port': kwargs.get('port', int(os.getenv('DB_PORT', 5432))),
            'user': kwargs.get('user', os.getenv('DB_USER', 'postgres')),
            'password': kwargs.get('password', os.getenv('DB_PASSWORD', 'auren_dev')),
            'database': kwargs.get('database', os.getenv('DB_NAME', 'auren_development')),
            'min_size': kwargs.get('min_size', 10),
            'max_size': kwargs.get('max_size', 20),
            'command_timeout': kwargs.get('command_timeout', 60),
        }
        
        try:
            # Create connection pool
            cls._instance = await asyncpg.create_pool(**connection_params)
            cls._initialized = True
            
            # Test the connection
            async with cls._instance.acquire() as conn:
                version = await conn.fetchval('SELECT version()')
                logger.info(f"Connected to PostgreSQL: {version}")
            
            return cls._instance
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            cls._instance = None
            cls._initialized = False
            raise
    
    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """
        Get the database connection pool
        
        Raises an error if the pool hasn't been initialized yet.
        This ensures we don't accidentally try to use the database
        before it's properly set up.
        """
        if cls._instance is None or not cls._initialized:
            raise RuntimeError(
                "Database connection not initialized. "
                "Call DatabaseConnection.initialize() first."
            )
        return cls._instance
    
    @classmethod
    async def close(cls):
        """
        Close the database connection pool
        
        Should be called when shutting down the application to ensure
        clean disconnection from the database.
        """
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
            cls._initialized = False
            logger.info("Database connection pool closed")
    
    @classmethod
    @asynccontextmanager
    async def acquire(cls):
        """
        Context manager for acquiring a database connection
        
        Usage:
            async with DatabaseConnection.acquire() as conn:
                result = await conn.fetch("SELECT * FROM users")
        """
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            yield conn
    
    @classmethod
    async def execute(cls, query: str, *args, timeout: float = None) -> str:
        """
        Execute a query that doesn't return results
        
        Useful for INSERT, UPDATE, DELETE operations.
        """
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)
    
    @classmethod
    async def fetch(cls, query: str, *args, timeout: float = None) -> list:
        """
        Execute a query and fetch all results
        
        Returns a list of Record objects that behave like dictionaries.
        """
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
    
    @classmethod
    async def fetchrow(cls, query: str, *args, timeout: float = None) -> Optional[asyncpg.Record]:
        """
        Execute a query and fetch a single row
        
        Returns None if no rows match the query.
        """
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
    
    @classmethod
    async def fetchval(cls, query: str, *args, column: int = 0, timeout: float = None) -> Any:
        """
        Execute a query and fetch a single value
        
        Useful for queries like "SELECT COUNT(*) FROM users"
        """
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)


# Convenience functions for common operations
async def init_db(**kwargs):
    """Initialize the database connection pool"""
    return await DatabaseConnection.initialize(**kwargs)


async def close_db():
    """Close the database connection pool"""
    await DatabaseConnection.close()


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_connection():
        """Test the database connection"""
        try:
            # Initialize connection
            await init_db()
            
            # Test basic query
            version = await DatabaseConnection.fetchval("SELECT version()")
            print(f"PostgreSQL version: {version}")
            
            # Test table query
            tables = await DatabaseConnection.fetch("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            
            print("\nTables in database:")
            for table in tables:
                print(f"  - {table['tablename']}")
            
            # Test with context manager
            async with DatabaseConnection.acquire() as conn:
                result = await conn.fetchval("SELECT COUNT(*) FROM user_facts")
                print(f"\nUser facts count: {result}")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await close_db()
    
    # Run the test
    asyncio.run(test_connection())
