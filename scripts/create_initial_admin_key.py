#!/usr/bin/env python3
"""
Create Initial Admin API Key for AUREN Security Enhancement
This script should be run once after deploying Section 9 to create the first admin key.
"""

import os
import sys
import asyncio
import asyncpg

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from section_9_security import (
    APIKeyManager,
    PHI_MASTER_KEY,
    lifespan,
    FastAPI
)


async def create_initial_admin_key():
    """Create the first admin API key for system setup"""
    
    # Database connection parameters from environment
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://auren_user:auren_secure_2025@localhost/auren_production"
    )
    
    print("Creating initial admin API key...")
    print(f"Connecting to database: {database_url}")
    
    try:
        # Create temporary app with lifespan for proper initialization
        app = FastAPI(lifespan=lifespan)
        
        # Initialize services using lifespan
        async with lifespan(app):
            # Create a direct connection for this operation
            db_pool = await asyncpg.create_pool(database_url, min_size=1, max_size=2)
            
            # Redis client for the API key manager
            import redis
            redis_client = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True
            )
            
            # Create API key manager
            api_key_manager = APIKeyManager(db_pool, redis_client)
            
            # Generate admin key
            result = await api_key_manager.create_api_key(
                user_id='admin',
                description='Initial admin API key',
                role='admin',
                created_by='system',
                rate_limit=1000  # Higher rate limit for admin
            )
            
            print("\n" + "="*60)
            print("✅ ADMIN API KEY CREATED SUCCESSFULLY")
            print("="*60)
            print(f"Key ID: {result['key_id']}")
            print(f"API Key: {result['api_key']}")
            print(f"Role: {result['role']}")
            print(f"User ID: {result['user_id']}")
            print("="*60)
            print("\n⚠️  IMPORTANT: Save this API key securely!")
            print("This key cannot be retrieved again.")
            print("\nUse this key in the Authorization header:")
            print(f"Authorization: Bearer {result['api_key']}")
            print("="*60)
            
            # Clean up
            await db_pool.close()
            redis_client.close()
            
    except Exception as e:
        print(f"\n❌ Error creating admin key: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running and accessible")
        print("2. Ensure Redis is running")
        print("3. Check DATABASE_URL and REDIS_URL environment variables")
        print("4. Ensure security tables have been created (run migration)")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the async function
    exit_code = asyncio.run(create_initial_admin_key())
    sys.exit(exit_code) 