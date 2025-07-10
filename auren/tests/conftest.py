"""Pytest configuration and fixtures for AUREN tests."""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment for all tests."""
    # Create temporary directories
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set test directories
        test_dirs = ['logs/system', 'data/protocols', 'data/media']
        for dir_path in test_dirs:
            Path(os.path.join(tmpdir, dir_path)).mkdir(parents=True, exist_ok=True)
        
        # Create test log file
        log_file = os.path.join(tmpdir, 'logs/system/auren.log')
        Path(log_file).touch()
        
        # Monkey patch environment variables
        monkeypatch.setenv('AUREN_DATA_DIR', tmpdir)
        monkeypatch.setenv('OPENAI_API_KEY', 'test_key')
        monkeypatch.setenv('WHATSAPP_ACCESS_TOKEN', 'test_token')
        monkeypatch.setenv('WHATSAPP_PHONE_ID', 'test_id')
        
        yield tmpdir

@pytest.fixture
def mock_facial_landmarks():
    """Provide correctly shaped facial landmarks for testing."""
    # 68-point facial landmarks (standard dlib format)
    landmarks = np.array([
        # Jaw line (17 points)
        [100, 200], [110, 210], [120, 220], [130, 230], [140, 240],
        [150, 250], [160, 260], [170, 270], [180, 280], [190, 270],
        [200, 260], [210, 250], [220, 240], [230, 230], [240, 220],
        [250, 210], [260, 200],
        # Right eyebrow (5 points)
        [120, 180], [130, 175], [140, 175], [150, 175], [160, 180],
        # Left eyebrow (5 points)
        [200, 180], [210, 175], [220, 175], [230, 175], [240, 180],
        # Nose bridge (4 points)
        [180, 190], [180, 200], [180, 210], [180, 220],
        # Nose tip (5 points)
        [160, 230], [170, 235], [180, 240], [190, 235], [200, 230],
        # Right eye (6 points)
        [130, 190], [140, 185], [150, 185], [160, 190], [150, 195], [140, 195],
        # Left eye (6 points)
        [200, 190], [210, 185], [220, 185], [230, 190], [220, 195], [210, 195],
        # Outer lip (12 points)
        [150, 260], [160, 255], [170, 250], [180, 250], [190, 250],
        [200, 255], [210, 260], [200, 270], [190, 275], [180, 275],
        [170, 275], [160, 270],
        # Inner lip (8 points)
        [160, 260], [170, 255], [180, 255], [190, 255], [200, 260],
        [190, 265], [180, 265], [170, 265]
    ], dtype=np.float64)
    
    return landmarks

@pytest.fixture
def mock_whatsapp_api():
    """Mock WhatsApp API for testing."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [{"id": "wamid.test123"}],
            "contacts": [{"input": "+1234567890", "wa_id": "1234567890"}]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
        yield mock_client

@pytest.fixture
def mock_openai():
    """Mock OpenAI API for testing."""
    with patch('openai.ChatCompletion.create') as mock_create:
        mock_create.return_value = {
            "choices": [{
                "message": {
                    "content": "Test response from AUREN"
                }
            }]
        }
        yield mock_create 