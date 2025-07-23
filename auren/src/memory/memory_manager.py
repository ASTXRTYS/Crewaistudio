"""Memory manager for coordinating all memory systems."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .episodic_memory import EpisodicMemory
from .semantic_memory import SemanticMemory
from .working_memory import WorkingMemory


class MemoryManager(BaseModel):
    """Central memory management system."""
    
    episodic: EpisodicMemory = Field(default_factory=EpisodicMemory)
    semantic: SemanticMemory = Field(default_factory=SemanticMemory)
    working: WorkingMemory = Field(default_factory=WorkingMemory)
    
    def add_episodic_memory(self, event: str, context: Dict[str, Any] = None) -> None:
        """Add an episodic memory."""
        from datetime import datetime
        self.episodic.add_memory(event, datetime.now(), context)
    
    def add_semantic_knowledge(self, key: str, value: Any, category: str = "general") -> None:
        """Add semantic knowledge."""
        self.semantic.add_knowledge(key, value, category)
    
    def add_working_item(self, item: Dict[str, Any]) -> None:
        """Add an item to working memory."""
        self.working.add_item(item)
    
    def search_all_memories(self, query: str) -> Dict[str, Any]:
        """Search across all memory systems."""
        results = {
            "episodic": self.episodic.search_memories(query),
            "semantic": self.semantic.search_knowledge(query),
            "working": [item for item in self.working.get_all_items() 
                       if query.lower() in str(item).lower()]
        }
        return results
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of all memory systems."""
        return {
            "episodic_count": len(self.episodic.memories),
            "semantic_count": len(self.semantic.knowledge),
            "working_count": len(self.working.get_all_items()),
            "categories": list(self.semantic.categories.keys())
        }
    
    def cleanup_memories(self, days: int = 30) -> None:
        """Clean up old memories."""
        self.episodic.clear_old_memories(days)
        self.working.clear_expired_items() 