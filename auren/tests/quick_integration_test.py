"""
Quick integration test for Module A + Module B
Tests PostgreSQL backend with intelligence systems
"""

import asyncio
import os
from pathlib import Path
from data_layer.connection import AsyncPostgresManager
from data_layer.memory_backend import PostgreSQLMemoryBackend
from data_layer.event_store import EventStore

async def test_integration():
    """Complete integration test"""
    print("🚀 Starting Module A + Module B integration test...")
    
    # Test 1: Database connection
    try:
        manager = AsyncPostgresManager()
        dsn = os.getenv('AUREN_DB_DSN', 'postgresql://auren_user:password@localhost:5432/auren')
        await manager.initialize(dsn)
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test 2: Backend initialization
    try:
        memory_backend = PostgreSQLMemoryBackend(manager)
        event_store = EventStore(manager)
        print("✅ Backend initialization successful")
    except Exception as e:
        print(f"❌ Backend initialization failed: {e}")
        await manager.close()
        return False
    
    # Test 3: Knowledge directory check
    knowledge_path = Path("auren/src/agents/Level 1 knowledge")
    if knowledge_path.exists():
        files = list(knowledge_path.rglob("*.md"))
        print(f"✅ Found {len(files)} knowledge files")
    else:
        print("❌ Knowledge directory not found")
        await manager.close()
        return False
    
    # Test 4: Basic storage and retrieval
    try:
        # Store test memory
        await memory_backend.store(
            agent_id="neuroscientist",
            user_id="system",
            memory_type="knowledge",
            content={"test": "integration working", "confidence": 0.9}
        )
        
        # Retrieve memories
        memories = await memory_backend.retrieve(
            agent_id="neuroscientist",
            user_id="system",
            limit=10
        )
        print(f"✅ Storage/retrieval successful: {len(memories)} items")
    except Exception as e:
        print(f"❌ Storage/retrieval failed: {e}")
        await manager.close()
        return False
    
    # Test 5: Event sourcing
    try:
        await event_store.append_event(
            stream_id="integration_test",
            event_type="test_complete",
            payload={"status": "success"}
        )
        print("✅ Event sourcing successful")
    except Exception as e:
        print(f"❌ Event sourcing failed: {e}")
        await manager.close()
        return False
    
    await manager.close()
    print("\n🎉 ALL INTEGRATION TESTS PASSED!")
    return True

if __name__ == "__main__":
    asyncio.run(test_integration())
