"""
Database connection management for AUREN.
Provides singleton connection pool with graceful error handling.
"""

import asyncpg
import logging
from typing import Optional
from contextlib import asynccontextmanager
import os
from .config import get_database_url

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Singleton database connection pool manager.
    Provides async PostgreSQL connections with proper pooling.
    """
    
    _instance: Optional['DatabaseManager'] = None
    _pool: Optional[asyncpg.Pool] = None
    
    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self) -> None:
        """Initialize the connection pool."""
        if self._pool is None:
            try:
                database_url = get_database_url()
                self._pool = await asyncpg.create_pool(
                    database_url,
                    min_size=1,
                    max_size=10,
                    command_timeout=30,
                    server_settings={
                        'application_name': 'auren_cognitive_twin'
                    }
                )
                logger.info("Database connection pool initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                raise
    
    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")
    
    @property
    def pool(self) -> asyncpg.Pool:
        """Get the connection pool."""
        if self._pool is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._pool
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a database connection."""
        async with self.pool.acquire() as conn:
            yield conn

# Global instance
db = DatabaseManager()
