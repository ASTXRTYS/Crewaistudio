import json
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    def __init__(self, database):
        self.db = database

    @abstractmethod
    def save(self, entity: T) -> str:
        pass

    @abstractmethod
    def get(self, id: str) -> Optional[T]:
        pass

    @abstractmethod
    def list(self) -> List[T]:
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        pass

    def _serialize_json(self, data: Any) -> Optional[str]:
        """Helper to serialize complex types to JSON strings"""
        return json.dumps(data) if data else None

    def _deserialize_json(self, data: Optional[str]) -> Any:
        """Helper to deserialize JSON strings"""
        return json.loads(data) if data else None
