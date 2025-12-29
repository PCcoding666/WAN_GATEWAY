import pytest
import os
import sys
from unittest.mock import MagicMock

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import Config

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv('DASHSCOPE_API_KEY', 'test_api_key')
    monkeypatch.setenv('TEXT_TO_VIDEO_ENDPOINT', 'https://api.example.com/t2v')
    monkeypatch.setenv('KEYFRAME_VIDEO_ENDPOINT', 'https://api.example.com/k2v')
    monkeypatch.setenv('IMAGE_TO_VIDEO_ENDPOINT', 'https://api.example.com/i2v')
    
    # Reload Config to pick up new env vars if necessary, 
    # but since Config reads env vars at class level, we might need to patch attributes directly
    monkeypatch.setattr(Config, 'DASHSCOPE_API_KEY', 'test_api_key')
    monkeypatch.setattr(Config, 'TEXT_TO_VIDEO_ENDPOINT', 'https://api.example.com/t2v')
    monkeypatch.setattr(Config, 'KEYFRAME_VIDEO_ENDPOINT', 'https://api.example.com/k2v')
    monkeypatch.setattr(Config, 'IMAGE_TO_VIDEO_ENDPOINT', 'https://api.example.com/i2v')

@pytest.fixture
def mock_response():
    """Mock requests response."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {}
    return mock
