import os
import re
from pathlib import Path

IMPORT_MAPPINGS = {
    r'from agents\.': 'from auren.agents.',
    r'from tools\.': 'from auren.tools.',
    r'from tasks\.': 'from auren.tasks.',
    r'from utils\.': 'from auren.utils.',
    r'from auren.repositories import': 'from auren.repositories import',
    r'import agents\.': 'import auren.agents.',
    r'import tools\.': 'import auren.tools.',
}

DB_FUNCTION_MAPPINGS = {
    'save_agent': 'agent_repo.save',
    'delete_agent': 'agent_repo.delete',
    'load_agent': 'agent_repo.get',
    'save_task': 'task_repo.save',
    'delete_task': 'task_repo.delete',
    'load_task': 'task_repo.get',
    'save_crew': 'crew_repo.save',
    'delete_crew': 'crew_repo.delete',
    'load_crew': 'crew_repo.get',
}

def refactor_file(filepath: Path):
    """Refactor a single Python file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix imports
    for old_pattern, new_pattern in IMPORT_MAPPINGS.items():
        content = re.sub(old_pattern, new_pattern, content)
    
    # Add repository imports if db_utils functions are used
    if any(func in content for func in DB_FUNCTION_MAPPINGS.keys()):
        if 'from auren.repositories import' not in content:
            # Add after other imports
            import_lines = []
            if 'save_agent' in content or 'delete_agent' in content or 'load_agent' in content:
                import_lines.append('from auren.repositories import Database, AgentRepository')
            if 'save_task' in content or 'delete_task' in content or 'load_task' in content:
                import_lines.append('from auren.repositories import TaskRepository')
            if 'save_crew' in content or 'delete_crew' in content or 'load_crew' in content:
                import_lines.append('from auren.repositories import CrewRepository')
            
            # Insert imports after first import block
            import_block = '\n'.join(import_lines) + '\n\n'
            content = re.sub(r'((?:from|import).*\n)+', r'\1' + import_block, content, count=1)
    
    # Replace DB function calls (this is simplified - you may need more context)
    # Add repository initialization where needed
    if 'class' in content and any(func in content for func in DB_FUNCTION_MAPPINGS.keys()):
        # Add __init__ method with repository initialization if not present
        class_pattern = r'(class\s+\w+.*?:)'
        init_code = '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = Database()
        self.agent_repo = AgentRepository(self.db)
        self.task_repo = TaskRepository(self.db)
        self.crew_repo = CrewRepository(self.db)
'''
        # More sophisticated logic needed here for proper placement
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Refactored: {filepath}")
        return True
    return False

def refactor_all():
    """Refactor all Python files in the project"""
    root = Path('/Users/Jason/Downloads/AUREN-Studio-main/auren')
    refactored_count = 0
    
    for py_file in root.rglob('*.py'):
        if 'venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
        if refactor_file(py_file):
            refactored_count += 1
    
    print(f"\n✅ Refactored {refactored_count} files")

if __name__ == "__main__":
    refactor_all() 