"""
LangGraph Integration Layer
Provides seamless integration between PostgreSQL memory backend and LangGraph agents
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .memory_backend import PostgreSQLMemoryBackend, MemoryType
from .event_store import EventStore, EventType

logger = logging.getLogger(__name__)

class AURENMemoryStorage:
    """
    Memory storage implementation for LangGraph agents
    Provides unlimited memory storage with PostgreSQL backend
    """
    
    def __init__(self, memory_backend: PostgreSQLMemoryBackend, agent_id: str):
        self.memory_backend = memory_backend
        self.agent_id = agent_id
    
    def save(self, value: Any, metadata: Dict[str, Any] = None) -> str:
        """Save a memory value with metadata"""
        return asyncio.create_task(self._async_save(value, metadata))
    
    async def _async_save(self, value: Any, metadata: Dict[str, Any] = None) -> str:
        """Async save implementation"""
        metadata = metadata or {}
        user_id = metadata.get('user_id', 'default_user')
        confidence = metadata.get('confidence', 0.5)
        memory_type = metadata.get('memory_type', MemoryType.OBSERVATION)
        
        content = {
            "value": value,
            "metadata": metadata
        }
        
        return await self.memory_backend.store_memory(
            agent_id=self.agent_id,
            memory_type=memory_type,
            content=content,
            user_id=user_id,
            confidence=confidence
        )
    
    def search(self, query: str, limit: int = 10, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search memories"""
        return asyncio.create_task(self._async_search(query, limit, metadata))
    
    async def _async_search(self, query: str, limit: int, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Async search implementation"""
        metadata = metadata or {}
        user_id = metadata.get('user_id', 'default_user')
        
        return await self.memory_backend.search_memories(
            agent_id=self.agent_id,
            query=query,
            user_id=user_id,
            limit=limit
        )
    
    def get(self, limit: int = 10, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get recent memories"""
        return asyncio.create_task(self._async_get(limit, metadata))
    
    async def _async_get(self, limit: int, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Async get implementation"""
        metadata = metadata or {}
        user_id = metadata.get('user_id', 'default_user')
        
        return await self.memory_backend.retrieve_memories(
            agent_id=self.agent_id,
            user_id=user_id,
            limit=limit
        )
    
    def clear(self) -> bool:
        """Clear all memories - soft delete for audit trail"""
        return asyncio.create_task(self._async_clear())
    
    async def _async_clear(self) -> bool:
        """Async clear implementation"""
        # Soft delete all memories for this agent
        async with self.memory_backend.connection() as conn:
            result = await conn.execute(
                "UPDATE agent_memories SET is_deleted = TRUE WHERE agent_id = $1",
                self.agent_id
            )
            return result == "UPDATE 1"

class AURENCrewMemoryIntegration:
    """
    Integration layer for LangGraph agents
    Provides factory methods for creating memory storage instances
    """
    
    def __init__(self, memory_backend: PostgreSQLMemoryBackend, event_store: EventStore):
        self.memory_backend = memory_backend
        self.event_store = event_store
    
    def create_agent_memory_storage(self, agent_id: str) -> AURENMemoryStorage:
        """Create memory storage for a specific agent"""
        return AURENMemoryStorage(self.memory_backend, agent_id)
    
    def create_neuroscientist_storage(self) -> AURENMemoryStorage:
        """Create memory storage for the Neuroscientist agent"""
        return self.create_agent_memory_storage("neuroscientist")
    
    def create_nutritionist_storage(self) -> AURENMemoryStorage:
        """Create memory storage for the Nutritionist agent"""
        return self.create_agent_memory_storage("nutritionist")
    
    def create_fitness_coach_storage(self) -> AURENMemoryStorage:
        """Create memory storage for the Fitness Coach agent"""
        return self.create_agent_memory_storage("fitness_coach")
    
    def create_physical_therapist_storage(self) -> AURENMemoryStorage:
        """Create memory storage for the Physical Therapist agent"""
        return self.create_agent_memory_storage("physical_therapist")
    
    def create_medical_esthetician_storage(self) -> AURENMemoryStorage:
        """Create memory storage for the Medical Esthetician agent"""
        return self.create_agent_memory_storage("medical_esthetician")
    
    async def get_agent_memory_count(self, agent_id: str, user_id: str) -> int:
        """Get count of memories for specific agent and user"""
        return await self.memory_backend.get_memory_count(agent_id, user_id)
    
    async def get_agent_recent_memories(self, agent_id: str, user_id: str, 
                                      days: int = 7) -> List[Dict[str, Any]]:
        """Get recent memories for specific agent and user"""
        return await self.memory_backend.get_recent_memories(agent_id, user_id, days)

# Migration utilities
class JSONToPostgreSQLMigrator:
    """
    Utility class for migrating from JSON file storage to PostgreSQL
    """
    
    def __init__(self, json_directory: str, memory_backend: PostgreSQLMemoryBackend, 
                 event_store: EventStore):
        self.json_directory = json_directory
        self.memory_backend = memory_backend
        self.event_store = event_store
    
    async def migrate_all(self, dry_run: bool = False) -> Dict[str, int]:
        """Migrate all JSON memories to PostgreSQL"""
        import os
        import json as json_lib
        
        migrated_count = 0
        
        # Check if directory exists
        if not os.path.exists(self.json_directory):
            return {"memories_migrated": 0, "error": "Directory not found"}
        
        # Process all JSON files
        for filename in os.listdir(self.json_directory):
            if filename.endswith('.json'):
                file_path = os.path.join(self.json_directory, filename)
                
                try:
                    with open(file_path, 'r') as f:
                        data = json_lib.load(f)
                    
                    if isinstance(data, list):
                        for memory in data:
                            if not dry_run:
                                await self._migrate_memory(memory)
                            migrated_count += 1
                    else:
                        if not dry_run:
                            await self._migrate_memory(data)
                        migrated_count += 1
                        
                except Exception as e:
                    logger.error(f"Error migrating {filename}: {e}")
        
        return {"memories_migrated": migrated_count}
    
    async def _migrate_memory(self, memory: Dict[str, Any]) -> None:
        """Migrate a single memory"""
        agent_id = memory.get('agent_id', 'unknown')
        user_id = memory.get('user_id', 'default_user')
        memory_type = MemoryType(memory.get('memory_type', 'observation'))
        content = memory.get('content', {})
        confidence = memory.get('confidence', 0.5)
        
        await self.memory_backend.store_memory(
            agent_id=agent_id,
            memory_type=memory_type,
            content=content,
            user_id=user_id,
            confidence=confidence
        )

# Example usage and testing
async def test_integration():
    """Test the complete integration"""
    from .connection import AsyncPostgresManager
    
    # Initialize components
    await AsyncPostgresManager.initialize("postgresql://localhost:5432/auren")
    
    event_store = EventStore()
    await event_store.initialize()
    
    memory_backend = PostgreSQLMemoryBackend(event_store)
    await memory_backend.initialize()
    
    # Create integration
    integration = AURENCrewMemoryIntegration(memory_backend, event_store)
    
    # Test with Neuroscientist
    neuroscientist_memory = integration.create_neuroscientist_storage()
    
    # Test memory storage
    memory_id = await neuroscientist_memory._async_save(
        value={"hrv": 45, "stress_level": "elevated"},
        metadata={
            "user_id": "test_user",
            "confidence": 0.85,
            "memory_type": MemoryType.ANALYSIS
        }
    )
    
    print(f"✅ Stored memory: {memory_id}")
    
    # Test retrieval
    memories = await neuroscientist_memory._async_get(limit=5, metadata={"user_id": "test_user"})
    print(f"✅ Retrieved {len(memories)} memories")
    
    # Test search
    search_results = await neuroscientist_memory._async_search("hrv", limit=5, metadata={"user_id": "test_user"})
    print(f"✅ Found {len(search_results)} search results")
    
    # Test memory count
    count = await integration.get_agent_memory_count("neuroscientist", "test_user")
    print(f"✅ Total memories: {count}")
    
    await AsyncPostgresManager.close()

if __name__ == "__main__":
    asyncio.run(test_integration())
