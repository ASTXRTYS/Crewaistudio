"""Working memory system for Auren 2.0"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field


class WorkingMemory(BaseModel):
    """Working memory for temporary information processing."""
    
    active_items: List[Dict[str, Any]] = Field(default_factory=list)
    max_items: int = Field(default=10)
    expiration_time: int = Field(default=300)  # 5 minutes in seconds
    
    def add_item(self, item: Dict[str, Any]) -> None:
        """Add an item to working memory."""
        item["timestamp"] = datetime.now().isoformat()
        item["id"] = len(self.active_items) + 1
        
        self.active_items.append(item)
        
        # Maintain memory limit
        if len(self.active_items) > self.max_items:
            self.active_items.pop(0)
    
    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get an item by ID."""
        for item in self.active_items:
            if item.get("id") == item_id:
                return item
        return None
    
    def remove_item(self, item_id: int) -> bool:
        """Remove an item by ID."""
        for i, item in enumerate(self.active_items):
            if item.get("id") == item_id:
                self.active_items.pop(i)
                return True
        return False
    
    def clear_expired_items(self) -> None:
        """Remove expired items from working memory."""
        cutoff = datetime.now() - timedelta(seconds=self.expiration_time)
        
        self.active_items = [
            item for item in self.active_items
            if datetime.fromisoformat(item["timestamp"]) > cutoff
        ]
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all active items."""
        self.clear_expired_items()
        return self.active_items.copy() 