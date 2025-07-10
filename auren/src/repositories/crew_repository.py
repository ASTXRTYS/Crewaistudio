import uuid
from typing import Any, Dict, List, Optional

from .base_repository import BaseRepository
from .database import Database


class CrewRepository(BaseRepository[Dict[str, Any]]):
    def save(self, crew_data: Dict[str, Any]) -> str:
        if "id" not in crew_data:
            crew_data["id"] = str(uuid.uuid4())

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO crews 
                (id, name, agents, tasks, process, verbose)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    crew_data["id"],
                    crew_data["name"],
                    self._serialize_json(crew_data.get("agents", [])),
                    self._serialize_json(crew_data.get("tasks", [])),
                    crew_data.get("process", "sequential"),
                    crew_data.get("verbose", True),
                ),
            )
        return crew_data["id"]

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM crews WHERE id = ?", (id,)).fetchone()

            if row:
                return self._row_to_dict(row)
        return None

    def list(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM crews").fetchall()
            return [self._row_to_dict(row) for row in rows]

    def delete(self, id: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM crews WHERE id = ?", (id,))
            return cursor.rowcount > 0

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get crew by name"""
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM crews WHERE name = ?", (name,)).fetchone()

            if row:
                return self._row_to_dict(row)
        return None

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert a database row to a dictionary"""
        return {
            "id": row["id"],
            "name": row["name"],
            "agents": self._deserialize_json(row["agents"]),
            "tasks": self._deserialize_json(row["tasks"]),
            "process": row["process"],
            "verbose": bool(row["verbose"]),
            "created_at": row["created_at"],
        }
