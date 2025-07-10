from typing import Optional, List, Dict, Any
import uuid
from .base_repository import BaseRepository
from .database import Database

class TaskRepository(BaseRepository[Dict[str, Any]]):
    def save(self, task_data: Dict[str, Any]) -> str:
        if 'id' not in task_data:
            task_data['id'] = str(uuid.uuid4())
        
        with self.db.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO tasks 
                (id, description, expected_output, agent_id, tools, async_execution)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                task_data['id'],
                task_data['description'],
                task_data.get('expected_output'),
                task_data.get('agent_id'),
                self._serialize_json(task_data.get('tools', [])),
                task_data.get('async_execution', False)
            ))
        return task_data['id']
    
    def get(self, id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM tasks WHERE id = ?', (id,)
            ).fetchone()
            
            if row:
                return self._row_to_dict(row)
        return None
    
    def list(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute('SELECT * FROM tasks').fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def delete(self, id: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.execute('DELETE FROM tasks WHERE id = ?', (id,))
            return cursor.rowcount > 0
    
    def get_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all tasks assigned to a specific agent"""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                'SELECT * FROM tasks WHERE agent_id = ?', (agent_id,)
            ).fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert a database row to a dictionary"""
        return {
            'id': row['id'],
            'description': row['description'],
            'expected_output': row['expected_output'],
            'agent_id': row['agent_id'],
            'tools': self._deserialize_json(row['tools']),
            'async_execution': bool(row['async_execution']),
            'created_at': row['created_at']
        }
