"""Episodic memory system for Auren 2.0"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class EpisodicMemory(BaseModel):
    """Episodic memory for storing and retrieving personal experiences."""
    
    memories: List[Dict[str, Any]] = Field(default_factory=list)
    max_memories: int = Field(default=1000)
    
    def add_memory(self, event: str, timestamp: datetime, context: Dict[str, Any] = None) -> None:
        """Add a new episodic memory."""
        memory = {
            "event": event,
            "timestamp": timestamp.isoformat(),
            "context": context or {},
            "id": len(self.memories) + 1
        }
        
        self.memories.append(memory)
        
        # Maintain memory limit
        if len(self.memories) > self.max_memories:
            self.memories.pop(0)
    
    def get_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent memories."""
        return self.memories[-limit:]
    
    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """Search memories by content."""
        results = []
        query_lower = query.lower()
        
        for memory in self.memories:
            if (query_lower in memory["event"].lower() or 
                any(query_lower in str(v).lower() for v in memory["context"].values())):
                results.append(memory)
        
        return results
    
    def clear_old_memories(self, days: int = 30) -> None:
        """Clear memories older than specified days."""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        self.memories = [
            memory for memory in self.memories
            if datetime.fromisoformat(memory["timestamp"]).timestamp() > cutoff
        ] 