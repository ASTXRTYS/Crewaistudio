#!/usr/bin/env python3
"""Simple admin API key creation script"""

import asyncio
import asyncpg
import secrets
import hashlib
from passlib.context import CryptContext
import json
import ulid

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_key():
    """Create admin API key directly in database"""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host='localhost',
            database='auren_production',
            user='auren_user',
            password='auren_secure_2025'
        )
        
        # Generate key components
        key_id = f"ak_{secrets.token_hex(6)}"
        raw_key = f"auren_{secrets.token_urlsafe(32)}"
        key_prefix = hashlib.sha256(raw_key.encode()).hexdigest()[:16]
        key_hash = pwd_context.hash(raw_key)
        
        # Insert into database
        await conn.execute("""
            INSERT INTO api_keys 
            (key_id, key_prefix, key_hash, user_id, description, role, created_by, rate_limit_per_minute)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, key_id, key_prefix, key_hash, 'admin', 'Initial admin API key', 'admin', 'system', 1000)
        
        print("\n" + "="*60)
        print("✅ ADMIN API KEY CREATED SUCCESSFULLY")
        print("="*60)
        print(f"Key ID: {key_id}")
        print(f"API Key: {raw_key}")
        print(f"Role: admin")
        print(f"User ID: admin")
        print("="*60)
        print("\n⚠️  IMPORTANT: Save this API key securely!")
        print("This key cannot be retrieved again.")
        print("\nUse this key in the Authorization header:")
        print(f"Authorization: Bearer {raw_key}")
        print("="*60)
        
        await conn.close()
        return 0
        
    except Exception as e:
        print(f"\n❌ Error creating admin key: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(create_admin_key()) 