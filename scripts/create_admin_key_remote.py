#!/usr/bin/env python3
"""Create admin API key with inline environment variables"""

import os
import sys
import asyncio
import asyncpg
import redis
from fastapi import FastAPI

# Set environment variables
os.environ['PHI_MASTER_KEY'] = 'OIixes55QW8WL7ky0Q7HDHYRTwKld8U0kQvrZnFrRhA='
os.environ['DATABASE_URL'] = 'postgresql://auren_user:auren_secure_2025@localhost/auren_production'
os.environ['REDIS_URL'] = 'redis://localhost:6379'

# Add the app directory to the Python path
sys.path.insert(0, '/opt/auren_deploy/app')

from section_9_security import APIKeyManager, lifespan, FastAPI

async def create_admin():
    """Create the first admin API key"""
    try:
        # Create temporary app
        app = FastAPI(lifespan=lifespan)
        
        # Initialize services
        async with lifespan(app):
            # Create direct connections
            db_pool = await asyncpg.create_pool(
                os.environ['DATABASE_URL'],
                min_size=1,
                max_size=2
            )
            
            redis_client = redis.from_url(
                os.environ['REDIS_URL'],
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
                rate_limit=1000
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
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(create_admin())
    sys.exit(exit_code) 