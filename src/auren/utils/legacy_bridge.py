"""Bridge between legacy and new code"""

def wrap_legacy_agent(legacy_agent_class):
    """Wrap legacy agent to work with new system"""
    class ModernizedAgent(legacy_agent_class):
        def __init__(self, *args, **kwargs):
            # Initialize with new repository pattern
            from auren.repositories import Database, AgentRepository
            self.db = Database()
            self.agent_repo = AgentRepository(self.db)
            super().__init__(*args, **kwargs)
    
    return ModernizedAgent

def migrate_legacy_imports(module_path: str):
    """Helper to migrate legacy imports to new namespace"""
    import importlib
    import sys
    
    try:
        # Try new import first
        module = importlib.import_module(f"auren.{module_path}")
        return module
    except ImportError:
        # Fallback to legacy import
        legacy_module = importlib.import_module(module_path)
        return legacy_module

def create_legacy_compatibility_layer():
    """Create compatibility layer for legacy code"""
    import sys
    from types import ModuleType
    
    # Create auren.legacy module for backward compatibility
    legacy_module = ModuleType('auren.legacy')
    sys.modules['auren.legacy'] = legacy_module
    
    # Add legacy imports that might be needed
    try:
        from auren.agents import my_agent
        setattr(legacy_module, 'MyAgent', my_agent.MyAgent)
    except ImportError:
        pass
    
    try:
        from auren.tools import IntentClassifierTool
        setattr(legacy_module, 'IntentClassifierTool', IntentClassifierTool)
    except ImportError:
        pass
    
    return legacy_module 