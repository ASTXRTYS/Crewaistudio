"""
Pytest configuration for AUREN AI Gateway tests.

Sets up proper import paths and shared fixtures.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Also add the src directory
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# Configure pytest
import pytest
import asyncio
from typing import Generator

# Configure async test support
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Shared test configuration
@pytest.fixture
def test_config():
    """Provide test configuration."""
    return {
        "redis_url": "redis://localhost:6379/15",  # Use test database
        "openai_api_key": "test-key",
        "daily_budget_limit": 10.0,
        "llama_endpoint": "http://localhost:8000"
    }

# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("LLAMA_ENDPOINT", "http://localhost:8000")
    monkeypatch.setenv("DAILY_BUDGET_LIMIT", "10.0") 