#!/usr/bin/env python3
"""
Test script for DigitalOcean PostgreSQL connection
Run this to verify your database configuration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_digitalocean_connection():
    """Test connection to DigitalOcean PostgreSQL"""
    
    print("🔍 Testing DigitalOcean PostgreSQL Connection...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("   Please set DATABASE_URL in your .env file")
        return False
    
    print(f"📡 Database URL: {database_url[:50]}...")
    
    try:
        import asyncpg
        
        # Test connection
        print("🔌 Attempting to connect...")
        conn = await asyncpg.connect(database_url)
        
        # Test basic query
        print("✅ Connection successful!")
        
        # Test schema
        print("📊 Testing database schema...")
        result = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        if result:
            print(f"📋 Found {len(result)} tables:")
            for row in result:
                print(f"   - {row['table_name']}")
        else:
            print("📋 No tables found (database is empty)")
        
        # Test AUREN-specific tables
        print("🧠 Checking for AUREN tables...")
        auren_tables = [
            'user_profiles',
            'biometric_entries', 
            'milestones',
            'pattern_insights'
        ]
        
        for table in auren_tables:
            exists = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = $1
                );
            """, table)
            
            status = "✅" if exists else "❌"
            print(f"   {status} {table}")
        
        await conn.close()
        print("🎉 All tests passed!")
        return True
        
    except ImportError:
        print("❌ asyncpg not installed")
        print("   Run: pip install asyncpg")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Check your DATABASE_URL format")
        print("   2. Verify your IP is in DigitalOcean trusted sources")
        print("   3. Ensure SSL mode is set to 'require'")
        print("   4. Check username/password are correct")
        return False

async def test_local_vs_remote():
    """Compare local vs remote database performance"""
    
    print("\n⚡ Performance Comparison Test...")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not configured")
        return
    
    try:
        import asyncpg
        import time
        
        # Test connection speed
        start_time = time.time()
        conn = await asyncpg.connect(database_url)
        connect_time = time.time() - start_time
        
        print(f"🔌 Connection time: {connect_time:.3f} seconds")
        
        # Test query speed
        start_time = time.time()
        await conn.fetch("SELECT 1")
        query_time = time.time() - start_time
        
        print(f"⚡ Query time: {query_time:.3f} seconds")
        
        await conn.close()
        
        # Performance assessment
        if connect_time < 0.5:
            print("✅ Connection speed: Excellent")
        elif connect_time < 1.0:
            print("✅ Connection speed: Good")
        else:
            print("⚠️  Connection speed: Slow (consider closer region)")
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")

def main():
    """Main test function"""
    print("🚀 AUREN DigitalOcean Database Test")
    print("=" * 50)
    
    # Test connection
    success = asyncio.run(test_digitalocean_connection())
    
    if success:
        # Test performance
        asyncio.run(test_local_vs_remote())
        
        print("\n🎯 Next Steps:")
        print("   1. Run: python setup_cognitive_twin.py")
        print("   2. Start AUREN: python start_auren.py")
        print("   3. Monitor database in DigitalOcean dashboard")
    else:
        print("\n🔧 Setup Required:")
        print("   1. Create DigitalOcean PostgreSQL cluster")
        print("   2. Update .env file with DATABASE_URL")
        print("   3. Add your IP to trusted sources")
        print("   4. Run this test again")

if __name__ == "__main__":
    main() 