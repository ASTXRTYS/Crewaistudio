"""
Database infrastructure for AUREN
Provides async PostgreSQL connection pool and utilities
"""

import asyncio
import asyncpg
from asyncpg.pool import Pool
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages PostgreSQL connections for AUREN
    Provides connection pooling and database initialization
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[Pool] = None
        
    async def initialize(self) -> Pool:
        """
        Initialize the database connection pool
        """
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database connection pool initialized")
            return self.pool
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def health_check(self) -> bool:
        """Check if database is healthy"""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False
    
    async def get_pool(self) -> Pool:
        """Get the database connection pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return self.pool
    
    async def execute_schema(self, schema_sql: str):
        """Execute SQL schema"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
            logger.info("Database schema executed successfully")

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def get_database_manager(database_url: str) -> DatabaseManager:
    """Get or create the global database manager"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url)
    return _db_manager
