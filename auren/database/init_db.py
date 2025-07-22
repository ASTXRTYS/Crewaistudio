#!/usr/bin/env python3
"""
Database initialization script for AUREN
Handles PostgreSQL database creation and schema setup
"""

import os
import asyncio
import asyncpg
from pathlib import Path
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Handles database creation and schema initialization for AUREN"""
    
    def __init__(self, 
                 host: str = None,
                 port: int = None,
                 user: str = None,
                 password: str = None,
                 database: str = None):
        """Initialize with database connection parameters"""
        # Use environment variables with fallbacks
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = port or int(os.getenv('DB_PORT', 5432))
        self.user = user or os.getenv('DB_USER', 'postgres')
        self.password = password or os.getenv('DB_PASSWORD', 'auren_dev')
        self.database = database or os.getenv('DB_NAME', 'auren_development')
        
        # Schema file path
        self.schema_file = Path(__file__).parent / 'init_schema.sql'
    
    async def database_exists(self) -> bool:
        """Check if the database already exists"""
        try:
            # Connect to default postgres database
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='postgres'
            )
            
            # Check if our database exists
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
                self.database
            )
            
            await conn.close()
            return exists
            
        except Exception as e:
            logger.error(f"Error checking database existence: {e}")
            raise
    
    async def create_database(self):
        """Create the database if it doesn't exist"""
        try:
            # Connect to default postgres database
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='postgres'
            )
            
            # Check if database exists
            if not await self.database_exists():
                # Create database
                await conn.execute(f'CREATE DATABASE {self.database}')
                logger.info(f"Created database: {self.database}")
            else:
                logger.info(f"Database already exists: {self.database}")
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    async def load_schema(self):
        """Load the schema from SQL file"""
        if not self.schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_file}")
        
        # Read and process schema file
        with open(self.schema_file, 'r') as f:
            schema_content = f.read()
        
        # Remove the CREATE DATABASE statement since we handle it in Python
        lines = schema_content.split('\n')
        filtered_lines = []
        skip_next = False
        
        for line in lines:
            # Skip CREATE DATABASE and \c commands
            if 'CREATE DATABASE' in line or line.strip().startswith('\\c'):
                skip_next = False
                continue
            if skip_next:
                skip_next = False
                continue
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    async def apply_schema(self):
        """Apply the schema to the database"""
        try:
            # Connect to our database
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            
            # Load schema
            schema = await self.load_schema()
            
            # Split by semicolons but handle multi-line statements
            statements = []
            current_statement = []
            
            for line in schema.split('\n'):
                current_statement.append(line)
                if line.strip().endswith(';'):
                    statement = '\n'.join(current_statement).strip()
                    if statement and not statement.startswith('--'):
                        statements.append(statement)
                    current_statement = []
            
            # Execute each statement
            for i, statement in enumerate(statements):
                if statement.strip():
                    try:
                        await conn.execute(statement)
                    except asyncpg.exceptions.DuplicateTableError:
                        # Table already exists, skip
                        pass
                    except Exception as e:
                        logger.warning(f"Error executing statement {i}: {e}")
                        logger.debug(f"Statement: {statement[:100]}...")
            
            logger.info("Schema applied successfully")
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error applying schema: {e}")
            raise
    
    async def insert_test_data(self):
        """Insert test data for development"""
        try:
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            
            # Check if test user already exists
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM user_profiles WHERE external_id = $1)",
                'test_user_001'
            )
            
            if not exists:
                # Insert test user
                await conn.execute("""
                    INSERT INTO user_profiles (external_id, profile_data)
                    VALUES ($1, $2)
                """, 'test_user_001', {
                    'name': 'Test User',
                    'preferences': {
                        'notifications': True,
                        'analysis_depth': 'detailed'
                    }
                })
                
                # Insert test biometric baseline
                await conn.execute("""
                    INSERT INTO biometric_baselines (user_id, metric_type, baseline_value, calculation_method)
                    VALUES ('test_user_001', 'hrv_rmssd', 55.0, 'rolling_7d_average')
                """)
                
                logger.info("Test data inserted successfully")
            else:
                logger.info("Test data already exists")
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error inserting test data: {e}")
            # Don't raise, test data is optional
    
    async def initialize(self, include_test_data: bool = True):
        """Run the complete initialization process"""
        logger.info("Starting database initialization...")
        
        # Create database if needed
        await self.create_database()
        
        # Apply schema
        await self.apply_schema()
        
        # Optionally insert test data
        if include_test_data:
            await self.insert_test_data()
        
        logger.info("Database initialization complete!")


# Convenience functions
async def init_database(**kwargs):
    """Initialize the database with given parameters"""
    initializer = DatabaseInitializer(**kwargs)
    await initializer.initialize()


async def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize AUREN database')
    parser.add_argument('--host', default=None, help='Database host')
    parser.add_argument('--port', type=int, default=None, help='Database port')
    parser.add_argument('--user', default=None, help='Database user')
    parser.add_argument('--password', default=None, help='Database password')
    parser.add_argument('--database', default=None, help='Database name')
    parser.add_argument('--no-test-data', action='store_true', help='Skip test data insertion')
    
    args = parser.parse_args()
    
    await init_database(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        include_test_data=not args.no_test_data
    )


if __name__ == "__main__":
    asyncio.run(main())
