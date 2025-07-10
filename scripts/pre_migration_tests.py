import os
import subprocess
import sys
import time

def test_streamlit_startup():
    """Ensure Streamlit can start without errors"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "src/auren/app/app.py", "--server.headless", "true"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def test_webhook_endpoint():
    """Test WhatsApp webhook is accessible"""
    try:
        import requests
        response = requests.get("http://localhost:8501/webhook?hub.mode=subscribe&hub.verify_token=test&hub.challenge=123")
        return response.status_code == 200
    except:
        return False

def test_all_tools_importable():
    """Verify all tools can be imported"""
    try:
        from auren.tools import (
            WhatsAppWebhookTool,
            IntentClassifierTool,
            JSONLoggerTool
        )
        return True
    except ImportError:
        return False

def test_repository_imports():
    """Test repository layer imports"""
    try:
        from auren.repositories import Database, AgentRepository, TaskRepository, CrewRepository
        return True
    except ImportError:
        return False

def test_package_structure():
    """Test that the package structure is correct"""
    import os
    required_paths = [
        "src/auren/__init__.py",
        "src/auren/app/__init__.py",
        "src/auren/app/app.py",
        "src/auren/repositories/__init__.py",
        "src/auren/tools/__init__.py",
        "src/auren/utils/__init__.py"
    ]
    
    for path in required_paths:
        if not os.path.exists(path):
            return False
    return True

# Run all tests
if __name__ == "__main__":
    tests = [
        ("Package Structure", test_package_structure),
        ("Repository Imports", test_repository_imports),
        ("Tool Imports", test_all_tools_importable),
        ("Streamlit Startup", test_streamlit_startup),
        ("Webhook Endpoint", test_webhook_endpoint)
    ]
    
    print("🧪 Running Pre-Migration Tests...")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            result = test_func()
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {name}")
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ ERROR {name}: {str(e)}")
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for migration.")
    else:
        print("⚠️  Some tests failed. Review before proceeding.") 