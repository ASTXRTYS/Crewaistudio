"""Base protocol with proper type annotations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic
from datetime import datetime
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseProtocol(ABC, Generic[T]):
    """Base class for all AUREN protocols with type safety."""
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> T:
        """Process protocol data and return typed result."""
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate input data."""
        pass
    
    @abstractmethod
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts for this protocol."""
        pass 