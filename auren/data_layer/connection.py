"""
Database connection management for AUREN Intelligence System
Handles PostgreSQL connections with connection pooling
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any
import asyncpg
from asyncpg.pool import Pool

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Manages PostgreSQL database connections with connection pooling
    """
    
    def __init__(self, 
                 database_url: Optional[str] = None,
                 min_connections: Optional[int] = None,
                 max_connections: Optional[int] = None,
                 connection_timeout: Optional[int] = None):
        """
        Initialize database connection manager
        
        Args:
            database_url: PostgreSQL connection string (defaults to env var or localhost)
            min_connections: Minimum pool connections (defaults to env var or 1)
            max_connections: Maximum pool connections (defaults to env var or 10)
            connection_timeout: Connection timeout in seconds (defaults to env var or 30)
        """
        # Use environment variables with fallback defaults
        self.database_url = database_url or os.getenv(
            'DATABASE_URL', 
            'postgresql://localhost:5432/auren'
        )
        self.min_connections = min_connections or int(
            os.getenv('DATABASE_MIN_CONNECTIONS', '1')
        )
        self.max_connections = max_connections or int(
            os.getenv('DATABASE_MAX_CONNECTIONS', '10')
        )
        self.connection_timeout = connection_timeout or int(
            os.getenv('DATABASE_CONNECTION_TIMEOUT', '30')
        )
        self.pool: Optional[Pool] = None
    
    async def initialize(self) -> bool:
        """
        Initialize the connection pool
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("🔌 Initializing PostgreSQL connection pool...")
            
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.min_connections,
                max_size=self.max_connections,
                command_timeout=self.connection_timeout,
                server_settings={
                    'application_name': 'auren_intelligence_system'
                }
            )
            
            # Test connection
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            logger.info("✅ PostgreSQL connection pool initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database connection: {e}")
            return False
    
    async def cleanup(self):
        """Clean up connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("🔌 Database connection pool closed")
    
    async def execute(self, query: str, *args) -> Any:
        """
        Execute a query
        
        Args:
            query: SQL query
            *args: Query arguments
            
        Returns:
            Query result
        """
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> list:
        """
        Fetch multiple rows
        
        Args:
            query: SQL query
            *args: Query arguments
            
        Returns:
            List of rows
        """
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """
        Fetch single row
        
        Args:
            query: SQL query
            *args: Query arguments
            
        Returns:
            Single row or None
        """
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args) -> Any:
        """
        Fetch single value
        
        Args:
            query: SQL query
            *args: Query arguments
            
        Returns:
            Single value or None
        """
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    def transaction(self):
        """
        Get a transaction context manager
        
        Returns:
            Transaction context manager
        """
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        return self.pool.transaction()
    
    @property
    def is_initialized(self) -> bool:
        """Check if connection pool is initialized"""
        return self.pool is not None


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_database_connection() -> DatabaseConnection:
    """
    Get global database connection instance
    
    Returns:
        Database connection instance
    """
    global _db_connection
    
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    
    return _db_connection


async def initialize_database() -> bool:
    """
    Initialize global database connection
    
    Returns:
        True if initialization successful
    """
    conn = get_database_connection()
    return await conn.initialize()


async def cleanup_database():
    """Clean up global database connection"""
    global _db_connection
    
    if _db_connection:
        await _db_connection.cleanup()
        _db_connection = None


# Database schema initialization
async def initialize_schema():
    """
    Initialize database schema for intelligence system
    """
    conn = get_database_connection()
    
    if not conn.is_initialized:
        await conn.initialize()
    
    # Create tables if they don't exist
    schema_queries = [
        """
        CREATE TABLE IF NOT EXISTS knowledge_items (
            id SERIAL PRIMARY KEY,
            knowledge_id VARCHAR(255) UNIQUE NOT NULL,
            agent_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            domain VARCHAR(100) NOT NULL,
            knowledge_type VARCHAR(50) NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            content JSONB NOT NULL,
            confidence FLOAT NOT NULL,
            evidence_sources JSONB NOT NULL,
            validation_status VARCHAR(50) NOT NULL,
            related_knowledge JSONB DEFAULT '[]',
            conflicts_with JSONB DEFAULT '[]',
            supports JSONB DEFAULT '[]',
            application_count INTEGER DEFAULT 0,
            success_rate FLOAT DEFAULT 0.0,
            last_applied TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            metadata JSONB DEFAULT '{}'
        )
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_knowledge_user ON knowledge_items (user_id);
        CREATE INDEX IF NOT EXISTS idx_knowledge_agent ON knowledge_items (agent_id);
        CREATE INDEX IF NOT EXISTS idx_knowledge_domain ON knowledge_items (domain);
        CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_items (knowledge_type);
        CREATE INDEX IF NOT EXISTS idx_knowledge_status ON knowledge_items (validation_status);
        CREATE INDEX IF NOT EXISTS idx_knowledge_created ON knowledge_items (created_at);
        """,
        
        """
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            stream_id VARCHAR(255) NOT NULL,
            stream_type VARCHAR(100) NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            event_data JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_events_stream ON events (stream_id);
        CREATE INDEX IF NOT EXISTS idx_events_type ON events (stream_type);
        CREATE INDEX IF NOT EXISTS idx_events_event_type ON events (event_type);
        CREATE INDEX IF NOT EXISTS idx_events_created ON events (created_at);
        """,
        
        """
        CREATE TABLE IF NOT EXISTS hypotheses (
            id SERIAL PRIMARY KEY,
            hypothesis_id VARCHAR(255) UNIQUE NOT NULL,
            agent_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            domain VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            prediction JSONB NOT NULL,
            confidence FLOAT NOT NULL,
            evidence_criteria JSONB NOT NULL,
            formed_at TIMESTAMP WITH TIME ZONE NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            status VARCHAR(50) NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_hypotheses_user ON hypotheses (user_id);
        CREATE INDEX IF NOT EXISTS idx_hypotheses_agent ON hypotheses (agent_id);
        CREATE INDEX IF NOT EXISTS idx_hypotheses_domain ON hypotheses (domain);
        CREATE INDEX IF NOT EXISTS idx_hypotheses_status ON hypotheses (status);
        CREATE INDEX IF NOT EXISTS idx_hypotheses_expires ON hypotheses (expires_at);
        """
    ]
    
    for query in schema_queries:
        await conn.execute(query)
    
    logger.info("✅ Database schema initialized successfully")


# Utility functions for testing
async def create_test_database():
    """
    Create a test database for testing purposes
    """
    test_conn = DatabaseConnection(
        database_url="postgresql://localhost:5432/auren_test",
        min_connections=1,
        max_connections=5
    )
    
    await test_conn.initialize()
    await initialize_schema()
    
    return test_conn


async def cleanup_test_database(conn: DatabaseConnection):
    """
    Clean up test database
    
    Args:
        conn: Database connection to clean up
    """
    if conn:
        await conn.cleanup()
