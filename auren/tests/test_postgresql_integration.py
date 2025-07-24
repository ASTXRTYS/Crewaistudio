"""
Comprehensive tests for PostgreSQL integration
Validates unlimited memory storage and performance
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
import tempfile
import json
import os

from data_layer.connection import AsyncPostgresManager
from data_layer.event_store import EventStore, EventType
from data_layer.memory_backend import PostgreSQLMemoryBackend, MemoryType
from data_layer.crewai_integration import AURENCrewMemoryIntegration, JSONToPostgreSQLMigrator

# Test configuration
TEST_DSN = "postgresql://localhost:5432/auren_test"

@pytest.fixture(scope="session")
async def db_setup():
    """Set up test database"""
    await AsyncPostgresManager.initialize(TEST_DSN)
    
    event_store = EventStore()
    await event_store.initialize()
    
    memory_backend = PostgreSQLMemoryBackend(event_store)
    await memory_backend.initialize()
    
    integration = AURENCrewMemoryIntegration(memory_backend, event_store)
    
    yield {
        'event_store': event_store,
        'memory_backend': memory_backend,
        'integration': integration
    }
    
    await AsyncPostgresManager.close()

@pytest.mark.asyncio
async def test_unlimited_memory_storage(db_setup):
    """Test that we can store more than 1000 memories"""
    memory_backend = db_setup['memory_backend']
    
    # Store 2000 memories (double the old limit)
    memory_ids = []
    for i in range(2000):
        memory_id = await memory_backend.store_memory(
            agent_id="test_agent",
            memory_type=MemoryType.OBSERVATION,
            content={"test": f"memory_{i}", "data": i},
            user_id="test_user",
            confidence=0.8
        )
        memory_ids.append(memory_id)
    
    # Verify all memories were stored
    count = await memory_backend.get_memory_count("test_agent", "test_user")
    assert count == 2000
    
    # Verify we can retrieve them
    memories = await memory_backend.retrieve_memories(
        agent_id="test_agent",
        user_id="test_user",
        limit=100
    )
    assert len(memories) == 100

@pytest.mark.asyncio
async def test_memory_search_performance(db_setup):
    """Test search performance with large datasets"""
    memory_backend = db_setup['memory_backend']
    
    # Store 1000 memories with searchable content
    for i in range(1000):
        await memory_backend.store_memory(
            agent_id="performance_agent",
            memory_type=MemoryType.ANALYSIS,
            content={
                "analysis": f"Performance analysis {i}",
                "keywords": ["performance", "optimization", f"test_{i}"],
                "metrics": {"speed": i * 10, "accuracy": 0.95}
            },
            user_id="performance_user",
            confidence=0.9
        )
    
    # Test search performance
    import time
    start_time = time.time()
    
    results = await memory_backend.search_memories(
        agent_id="performance_agent",
        query="performance optimization",
        user_id="performance_user",
        limit=50
    )
    
    search_time = time.time() - start_time
    
    assert len(results) > 0
    assert search_time < 0.1  # Should be under 100ms

@pytest.mark.asyncio
async def test_event_sourcing(db_setup):
    """Test event sourcing capabilities"""
    event_store = db_setup['event_store']
    
    # Create test stream
    stream_id = str(uuid.uuid4())
    
    # Append events
    events = []
    for i in range(10):
        event = await event_store.append_event(
            stream_id=stream_id,
            event_type=EventType.MEMORY_CREATED,
            payload={"memory_id": f"mem_{i}", "content": f"test_{i}"}
        )
        events.append(event)
    
    # Verify events were stored
    stored_events = await event_store.get_stream_events(stream_id)
    assert len(stored_events) == 10
    
    # Verify event ordering
    for i, event in enumerate(stored_events):
        assert event.version == i + 1

@pytest.mark.asyncio
async def test_concurrent_access(db_setup):
    """Test concurrent memory operations"""
    memory_backend = db_setup['memory_backend']
    
    async def store_memory_async(agent_id: str, memory_index: int):
        return await memory_backend.store_memory(
            agent_id=agent_id,
            memory_type=MemoryType.OBSERVATION,
            content={"concurrent_test": memory_index},
            user_id="concurrent_user",
            confidence=0.7
        )
    
    # Store 100 memories concurrently
    tasks = []
    for i in range(100):
        tasks.append(store_memory_async("concurrent_agent", i))
    
    results = await asyncio.gather(*tasks)
    assert len(results) == 100
    
    # Verify all were stored
    count = await memory_backend.get_memory_count("concurrent_agent", "concurrent_user")
    assert count == 100

@pytest.mark.asyncio
async def test_memory_confidence_scoring(db_setup):
    """Test confidence scoring and filtering"""
    memory_backend = db_setup['memory_backend']
    
    # Store memories with different confidence levels
    for i in range(10):
        confidence = i / 10.0  # 0.0 to 0.9
        await memory_backend.store_memory(
            agent_id="confidence_agent",
            memory_type=MemoryType.INSIGHT,
            content={"insight": f"insight_{i}", "confidence": confidence},
            user_id="confidence_user",
            confidence=confidence
        )
    
    # Test filtering by confidence
    high_confidence_memories = await memory_backend.retrieve_memories(
        agent_id="confidence_agent",
        user_id="confidence_user",
        min_confidence=0.7,
        limit=100
    )
    
    assert len(high_confidence_memories) == 3  # 0.7, 0.8, 0.9

@pytest.mark.asyncio
async def test_crewai_integration(db_setup):
    """Test CrewAI integration layer"""
    integration = db_setup['integration']
    
    # Test agent-specific storage
    neuroscientist_storage = integration.create_neuroscientist_storage()
    
    # Store memories for different agents
    await neuroscientist_storage._async_save(
        value={"neuroscience": "brain_optimization"},
        metadata={"user_id": "integration_user", "confidence": 0.9}
    )
    
    # Test retrieval
    memories = await neuroscientist_storage._async_get(
        limit=10,
        metadata={"user_id": "integration_user"}
    )
    
    assert len(memories) > 0
    assert "neuroscience" in str(memories[0]["content"])

@pytest.mark.asyncio
async def test_json_migration(db_setup):
    """Test migration from JSON to PostgreSQL"""
    memory_backend = db_setup['memory_backend']
    event_store = db_setup['event_store']
    
    # Create temporary JSON files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test JSON files
        json_data = [
            {
                "agent_id": "migrator_agent",
                "user_id": "migration_user",
                "memory_type": "fact",
                "content": {"fact": "migration_test"},
                "confidence": 0.8
            }
        ]
        
        json_file = os.path.join(temp_dir, "test_memories.json")
        with open(json_file, 'w') as f:
            json.dump(json_data, f)
        
        # Run migration
        migrator = JSONToPostgreSQLMigrator(temp_dir, memory_backend, event_store)
        result = await migrator.migrate_all()
        
        assert result["memories_migrated"] == 1
        
        # Verify migration
        count = await memory_backend.get_memory_count("migrator_agent", "migration_user")
        assert count == 1

@pytest.mark.asyncio
async def test_memory_expiration(db_setup):
    """Test memory expiration functionality"""
    memory_backend = db_setup['memory_backend']
    
    # Store memories with different timestamps
    now = datetime.utcnow()
    
    # Store recent memory
    await memory_backend.store_memory(
        agent_id="expiration_agent",
        memory_type=MemoryType.OBSERVATION,
        content={"recent": "data"},
        user_id="expiration_user",
        confidence=0.8
    )
    
    # Test recent memory retrieval
    recent_memories = await memory_backend.get_recent_memories(
        agent_id="expiration_agent",
        user_id="expiration_user",
        days=1
    )
    
    assert len(recent_memories) == 1

@pytest.mark.asyncio
async def test_full_text_search(db_setup):
    """Test full-text search capabilities"""
    memory_backend = db_setup['memory_backend']
    
    # Store memories with searchable content
    content = {
        "analysis": "This is a comprehensive analysis of HRV patterns",
        "findings": "The user shows elevated stress levels",
        "recommendations": "Consider meditation and better sleep hygiene"
    }
    
    await memory_backend.store_memory(
        agent_id="search_agent",
        memory_type=MemoryType.ANALYSIS,
        content=content,
        user_id="search_user",
        confidence=0.9
    )
    
    # Test search
    results = await memory_backend.search_memories(
        agent_id="search_agent",
        query="HRV stress meditation",
        user_id="search_user",
        limit=10
    )
    
    assert len(results) > 0
    assert "HRV" in str(results[0]["content"])

@pytest.mark.asyncio
async def test_memory_update_and_delete(db_setup):
    """Test memory update and delete operations"""
    memory_backend = db_setup['memory_backend']
    
    # Store initial memory
    memory_id = await memory_backend.store_memory(
        agent_id="update_agent",
        memory_type=MemoryType.OBSERVATION,
        content={"initial": "data"},
        user_id="update_user",
        confidence=0.5
    )
    
    # Update memory
    success = await memory_backend.update_memory(
        memory_id=memory_id,
        content={"updated": "data"},
        confidence=0.8
    )
    assert success
    
    # Verify update
    memories = await memory_backend.retrieve_memories(
        agent_id="update_agent",
        user_id="update_user",
        limit=1
    )
    assert memories[0]["content"]["updated"] == "data"
    assert memories[0]["confidence_score"] == 0.8
    
    # Delete memory
    success = await memory_backend.delete_memory(memory_id)
    assert success
    
    # Verify deletion
    memories = await memory_backend.retrieve_memories(
        agent_id="update_agent",
        user_id="update_user",
        limit=1
    )
    assert len(memories) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
