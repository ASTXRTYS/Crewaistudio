#!/usr/bin/env python3
"""
Database initialization script for AUREN
This script sets up all the necessary PostgreSQL tables and extensions
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_postgres_connection(conn_params):
    """
    Check if we can connect to PostgreSQL server
    """
    try:
        # Try to connect to postgres database first
        test_params = conn_params.copy()
        test_params['database'] = 'postgres'
        
        conn = await asyncpg.connect(**test_params)
        await conn.close()
        logger.info("✓ PostgreSQL server is accessible")
        return True
    except Exception as e:
        logger.error(f"✗ Cannot connect to PostgreSQL: {e}")
        return False


async def create_database_if_not_exists(conn_params):
    """
    Create the auren_development database if it doesn't exist
    """
    db_name = conn_params['database']
    
    # Connect to postgres database to create our database
    admin_params = conn_params.copy()
    admin_params['database'] = 'postgres'
    
    try:
        conn = await asyncpg.connect(**admin_params)
        
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            db_name
        )
        
        if not exists:
            # Create database
            # Note: asyncpg doesn't support CREATE DATABASE in a transaction
            await conn.execute(f'CREATE DATABASE {db_name}')
            logger.info(f"✓ Created database '{db_name}'")
        else:
            logger.info(f"✓ Database '{db_name}' already exists")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ Error creating database: {e}")
        return False


async def run_schema_file(conn_params, schema_path):
    """
    Execute the SQL schema file
    """
    try:
        # Read the schema file
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Connect to our database
        conn = await asyncpg.connect(**conn_params)
        
        # Split the schema into individual statements
        # This is a simple approach - for production, consider a proper SQL parser
        statements = []
        current_statement = []
        
        for line in schema_sql.split('\n'):
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('--'):
                continue
            
            # Handle \c command specially
            if stripped.startswith('\\c'):
                continue  # We're already connected to the right database
            
            current_statement.append(line)
            
            # Simple statement delimiter detection
            if stripped.endswith(';') and not stripped.startswith('CREATE OR REPLACE FUNCTION'):
                statements.append('\n'.join(current_statement))
                current_statement = []
        
        # Handle functions and triggers that span multiple lines
        if current_statement:
            statements.append('\n'.join(current_statement))
        
        # Execute each statement
        success_count = 0
        for i, statement in enumerate(statements, 1):
            if not statement.strip():
                continue
                
            try:
                await conn.execute(statement)
                success_count += 1
                
                # Log creation of major objects
                if 'CREATE TABLE' in statement:
                    table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip()
                    table_name = table_name.replace('IF NOT EXISTS', '').strip()
                    logger.info(f"  ✓ Created table {table_name}")
                elif 'CREATE INDEX' in statement:
                    index_name = statement.split('CREATE INDEX')[1].split(' ON ')[0].strip()
                    logger.info(f"  ✓ Created index {index_name}")
                    
            except asyncpg.DuplicateObjectError as e:
                # Object already exists, that's fine
                logger.debug(f"  → Object already exists: {str(e)[:50]}...")
            except Exception as e:
                logger.error(f"  ✗ Error executing statement {i}: {e}")
                logger.debug(f"    Statement: {statement[:100]}...")
        
        await conn.close()
        
        logger.info(f"✓ Successfully executed {success_count} SQL statements")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error running schema file: {e}")
        return False


async def verify_tables(conn_params):
    """
    Verify that all expected tables were created
    """
    expected_tables = [
        'user_profiles',
        'user_facts',
        'conversation_insights',
        'biometric_baselines',
        'biometric_readings',
        'hypotheses',
        'consultation_nodes',
        'consultation_edges',
        'events',
        'milestones',
        'biometric_timeline'
    ]
    
    try:
        conn = await asyncpg.connect(**conn_params)
        
        # Get all tables in public schema
        tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        table_names = [t['tablename'] for t in tables]
        
        logger.info("\n✓ Database tables created:")
        for table in expected_tables:
            if table in table_names:
                logger.info(f"  ✓ {table}")
            else:
                logger.warning(f"  ✗ {table} (missing)")
        
        # Check for test data
        test_user = await conn.fetchrow(
            "SELECT * FROM user_profiles WHERE external_id = 'test_user_001'"
        )
        
        if test_user:
            logger.info("\n✓ Test data inserted successfully")
            logger.info(f"  Test user ID: {test_user['user_id']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ Error verifying tables: {e}")
        return False


async def main():
    """
    Main initialization function
    """
    logger.info("=== AUREN Database Initialization ===\n")
    
    # Get connection parameters
    conn_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'auren_dev'),
        'database': os.getenv('DB_NAME', 'auren_development')
    }
    
    logger.info(f"Connecting to PostgreSQL at {conn_params['host']}:{conn_params['port']}")
    
    # Step 1: Check PostgreSQL connection
    if not await check_postgres_connection(conn_params):
        logger.error("\nPlease ensure PostgreSQL is running and accessible.")
        logger.error("If using Docker, run:")
        logger.error("  docker run -d --name postgres-auren \\")
        logger.error("    -e POSTGRES_PASSWORD=auren_dev \\")
        logger.error("    -e POSTGRES_DB=auren_development \\")
        logger.error("    -p 5432:5432 \\")
        logger.error("    postgres:15-alpine")
        return False
    
    # Step 2: Create database if needed
    if not await create_database_if_not_exists(conn_params):
        return False
    
    # Step 3: Run schema file
    schema_path = Path(__file__).parent / 'init_schema.sql'
    if not schema_path.exists():
        logger.error(f"✗ Schema file not found: {schema_path}")
        return False
    
    logger.info(f"\nApplying schema from {schema_path}")
    if not await run_schema_file(conn_params, schema_path):
        return False
    
    # Step 4: Verify tables
    if not await verify_tables(conn_params):
        return False
    
    logger.info("\n✓ Database initialization completed successfully!")
    logger.info("\nYou can now connect to the database with:")
    logger.info(f"  psql -h {conn_params['host']} -p {conn_params['port']} "
                f"-U {conn_params['user']} -d {conn_params['database']}")
    
    return True


if __name__ == "__main__":
    # Run the initialization
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
