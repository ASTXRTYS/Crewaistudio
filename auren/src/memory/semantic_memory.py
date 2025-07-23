"""Semantic memory system for Auren 2.0"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class SemanticMemory(BaseModel):
    """Semantic memory for storing facts and knowledge."""
    
    knowledge: Dict[str, Any] = Field(default_factory=dict)
    categories: Dict[str, List[str]] = Field(default_factory=dict)
    
    def add_knowledge(self, key: str, value: Any, category: str = "general") -> None:
        """Add a piece of knowledge."""
        self.knowledge[key] = value
        
        if category not in self.categories:
            self.categories[category] = []
        
        if key not in self.categories[category]:
            self.categories[category].append(key)
    
    def get_knowledge(self, key: str) -> Any:
        """Retrieve knowledge by key."""
        return self.knowledge.get(key)
    
    def get_category_knowledge(self, category: str) -> Dict[str, Any]:
        """Get all knowledge in a category."""
        if category not in self.categories:
            return {}
        
        return {key: self.knowledge[key] for key in self.categories[category] if key in self.knowledge}
    
    def search_knowledge(self, query: str) -> Dict[str, Any]:
        """Search knowledge by query."""
        results = {}
        query_lower = query.lower()
        
        for key, value in self.knowledge.items():
            if (query_lower in key.lower() or 
                query_lower in str(value).lower()):
                results[key] = value
        
        return results 