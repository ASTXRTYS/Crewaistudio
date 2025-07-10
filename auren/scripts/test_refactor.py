def test_imports():
    """Test all critical imports work"""
    try:
        from auren.repositories import Database, AgentRepository
        from auren.agents.my_agent import MyAgent
        from auren.tools.WhatsAppWebhookTool import WhatsAppWebhookTool
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_repository_operations():
    """Test basic repository operations"""
    from auren.repositories import Database, AgentRepository
    
    db = Database()
    agent_repo = AgentRepository(db)
    
    # Test save
    agent_id = agent_repo.save({
        'name': 'Test Agent',
        'role': 'Tester',
        'goal': 'Test the system'
    })
    
    # Test get
    agent = agent_repo.get(agent_id)
    assert agent['name'] == 'Test Agent'
    
    # Test delete
    assert agent_repo.delete(agent_id) == True
    
    print("✅ Repository operations working")
    return True

if __name__ == "__main__":
    test_imports()
    test_repository_operations() 