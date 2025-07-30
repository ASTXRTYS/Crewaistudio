import redis
import asyncpg
import asyncio

async def test():
    # Test Redis
    try:
        r = redis.from_url("redis://redis:6379")
        print(f"✅ Redis: {r.ping()}")
    except Exception as e:
        print(f"❌ Redis: {e}")
    
    # Test PostgreSQL
    try:
        conn = await asyncpg.connect(
            "postgresql://postgres:example@postgres:5432/neuros"
        )
        result = await conn.fetchval("SELECT 1")
        print(f"✅ PostgreSQL: {result}")
        await conn.close()
    except Exception as e:
        print(f"❌ PostgreSQL: {e}")

asyncio.run(test()) 