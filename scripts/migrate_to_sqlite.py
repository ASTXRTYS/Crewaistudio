import json
import os
import logging
from datetime import datetime
from auren.repositories import Database, AgentRepository, TaskRepository, CrewRepository

class DatabaseMigrator:
    def __init__(self):
        self.db = Database()
        self.agent_repo = AgentRepository(self.db)
        self.task_repo = TaskRepository(self.db)
        self.crew_repo = CrewRepository(self.db)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def migrate_from_json(self, json_path: str = 'crew_database.json'):
        """Migrate from JSON to SQLite"""
        if not os.path.exists(json_path):
            self.logger.warning(f"No JSON database found at {json_path}")
            return False
        
        # Backup original
        backup_path = f"data/backups/crew_database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        os.rename(json_path, backup_path)
        self.logger.info(f"Backed up original to {backup_path}")
        
        # Load JSON data
        with open(backup_path, 'r') as f:
            data = json.load(f)
        
        # Migrate agents
        agent_count = 0
        for agent_id, agent_data in data.get('agents', {}).items():
            agent_data['id'] = agent_id
            self.agent_repo.save(agent_data)
            agent_count += 1
        
        # Migrate tasks
        task_count = 0
        for task_id, task_data in data.get('tasks', {}).items():
            task_data['id'] = task_id
            self.task_repo.save(task_data)
            task_count += 1
        
        # Migrate crews
        crew_count = 0
        for crew_id, crew_data in data.get('crews', {}).items():
            crew_data['id'] = crew_id
            self.crew_repo.save(crew_data)
            crew_count += 1
        
        self.logger.info(f"✅ Migration complete: {agent_count} agents, {task_count} tasks, {crew_count} crews")
        return True
    
    def verify_migration(self):
        """Verify data integrity after migration"""
        agents = self.agent_repo.list()
        tasks = self.task_repo.list()
        crews = self.crew_repo.list()
        
        print(f"\nDatabase Status:")
        print(f"- Agents: {len(agents)}")
        print(f"- Tasks: {len(tasks)}")
        print(f"- Crews: {len(crews)}")
        
        return len(agents) > 0 or len(tasks) > 0 or len(crews) > 0

if __name__ == "__main__":
    migrator = DatabaseMigrator()
    if migrator.migrate_from_json():
        migrator.verify_migration() 