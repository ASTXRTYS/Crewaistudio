"""Temporary compatibility layer for legacy db_utils calls"""
from auren.repositories import Database, AgentRepository, TaskRepository, CrewRepository

# Global instances for compatibility
_db = Database()
_agent_repo = AgentRepository(_db)
_task_repo = TaskRepository(_db)
_crew_repo = CrewRepository(_db)

def save_agent(agent_data):
    """Legacy save_agent function"""
    if hasattr(agent_data, 'to_dict'):
        agent_data = agent_data.to_dict()
    return _agent_repo.save(agent_data)

def delete_agent(agent_id):
    """Legacy delete_agent function"""
    return _agent_repo.delete(agent_id)

def load_agent(agent_id):
    """Legacy load_agent function"""
    return _agent_repo.get(agent_id)

def save_task(task_data):
    """Legacy save_task function"""
    if hasattr(task_data, 'to_dict'):
        task_data = task_data.to_dict()
    return _task_repo.save(task_data)

def delete_task(task_id):
    """Legacy delete_task function"""
    return _task_repo.delete(task_id)

def load_task(task_id):
    """Legacy load_task function"""
    return _task_repo.get(task_id)

def save_crew(crew_data):
    """Legacy save_crew function"""
    if hasattr(crew_data, 'to_dict'):
        crew_data = crew_data.to_dict()
    return _crew_repo.save(crew_data)

def delete_crew(crew_id):
    """Legacy delete_crew function"""
    return _crew_repo.delete(crew_id)

def load_crew(crew_id):
    """Legacy load_crew function"""
    return _crew_repo.get(crew_id) 