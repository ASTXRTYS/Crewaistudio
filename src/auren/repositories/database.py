import sqlite3
from contextlib import contextmanager
from pathlib import Path

class Database:
    def __init__(self, db_path: str = "data/auren.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        with self.get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    goal TEXT,
                    backstory TEXT,
                    tools TEXT,  -- JSON array
                    llm_config TEXT,  -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    expected_output TEXT,
                    agent_id TEXT,
                    tools TEXT,  -- JSON array
                    async_execution BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents(id)
                );
                
                CREATE TABLE IF NOT EXISTS crews (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    agents TEXT NOT NULL,  -- JSON array of agent IDs
                    tasks TEXT NOT NULL,   -- JSON array of task IDs
                    process TEXT DEFAULT 'sequential',
                    verbose BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);
                CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id);
                CREATE INDEX IF NOT EXISTS idx_crews_name ON crews(name);
            ''')
