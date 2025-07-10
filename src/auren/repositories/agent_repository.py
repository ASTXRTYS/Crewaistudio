from typing import Optional, List, Dict, Any
import uuid
from .base_repository import BaseRepository
from .database import Database

class AgentRepository(BaseRepository[Dict[str, Any]]):
    def save(self, agent_data: Dict[str, Any]) -> str:
        if 'id' not in agent_data:
            agent_data['id'] = str(uuid.uuid4())
        
        with self.db.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO agents 
                (id, name, role, goal, backstory, tools, llm_config)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent_data['id'],
                agent_data['name'],
                agent_data['role'],
                agent_data.get('goal'),
                agent_data.get('backstory'),
                self._serialize_json(agent_data.get('tools', [])),
                self._serialize_json(agent_data.get('llm_config', {}))
            ))
        return agent_data['id']
    
    def get(self, id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM agents WHERE id = ?', (id,)
            ).fetchone()
            
            if row:
                return self._row_to_dict(row)
        return None
    
    def list(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute('SELECT * FROM agents').fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def delete(self, id: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.execute('DELETE FROM agents WHERE id = ?', (id,))
            return cursor.rowcount > 0
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert a database row to a dictionary"""
        return {
            'id': row['id'],
            'name': row['name'],
            'role': row['role'],
            'goal': row['goal'],
            'backstory': row['backstory'],
            'tools': self._deserialize_json(row['tools']),
            'llm_config': self._deserialize_json(row['llm_config']),
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }
