#!/usr/bin/env python3
"""
Test database connection before running knowledge loader
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data_layer.connection import get_database_connection, initialize_schema


async def test_connection():
    """Test database connection and schema"""
    print("Testing PostgreSQL connection...")
    
    try:
        # Get connection
        db = get_database_connection()
        
        # Initialize connection
        success = await db.initialize()
        if not success:
            print("❌ Failed to initialize database connection")
            print("Make sure PostgreSQL is running and accessible")
            return False
        
        print("✅ Database connection successful")
        
        # Initialize schema
        print("\nInitializing database schema...")
        await initialize_schema()
        print("✅ Database schema initialized")
        
        # Test query
        result = await db.fetchval("SELECT COUNT(*) FROM knowledge_items")
        print(f"\nCurrent knowledge items in database: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is installed and running")
        print("2. Create the 'auren' database: createdb auren")
        print("3. Check connection string in data_layer/connection.py")
        print("   Default: postgresql://localhost:5432/auren")
        return False
    
    finally:
        if db:
            await db.cleanup()


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1) 