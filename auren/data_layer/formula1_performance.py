import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from data_layer.memory_backend import PostgreSQLMemoryBackend
from data_layer.event_store import EventStore

logger = logging.getLogger(__name__)

@dataclass
class Formula1DatabaseConfig:
    """Configuration for Formula1 database operations."""
    host: str = "localhost"
    port: int = 5432
    database: str = "auren_db"
    user: str = "auren_user"
    password: str = "auren_secure_password"
    pool_size: int = 20
    max_overflow: int = 30

class Formula1AgentOrchestrator:
    """Orchestrates Formula1 performance data and agent interactions."""
    
    def __init__(self, memory_backend: PostgreSQLMemoryBackend, event_store: EventStore):
        self.memory_backend = memory_backend
        self.event_store = event_store
        logger.info("Formula1AgentOrchestrator initialized")
    
    async def store_performance_data(self, agent_id: str, data: Dict[str, Any]) -> bool:
        """Store Formula1 performance data for an agent."""
        try:
            await self.memory_backend.store_memory(
                agent_id=agent_id,
                memory_type="performance",
                content=data,
                user_id="system"
            )
            logger.info(f"Performance data stored for agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store performance data: {e}")
            return False
    
    async def get_performance_data(self, agent_id: str, limit: int = 100) -> list:
        """Retrieve performance data for an agent."""
        try:
            memories = await self.memory_backend.get_memories(
                agent_id=agent_id,
                memory_type="performance",
                limit=limit
            )
            logger.info(f"Retrieved {len(memories)} performance records for {agent_id}")
            return memories
        except Exception as e:
            logger.error(f"Failed to retrieve performance data: {e}")
            return []
