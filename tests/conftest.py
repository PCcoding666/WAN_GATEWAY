"""
pytest configuration and fixtures for the text-to-video application tests.
"""
import pytest
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.config import Config
from src.text_to_video_service import TextToVideoService

@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing."""
    return "sk-test-key-for-unit-tests"

@pytest.fixture
def service(mock_api_key):
    """Create a TextToVideoService instance for testing."""
    return TextToVideoService(api_key=mock_api_key)

@pytest.fixture
def valid_prompt():
    """Provide a valid test prompt."""
    return "A beautiful sunset over mountains with birds flying in the sky"

@pytest.fixture
def mock_success_response():
    """Mock successful API response."""
    return {
        "output": {
            "task_id": "test-task-123",
            "task_status": "SUCCEEDED", 
            "video_url": "https://example.com/test-video.mp4"
        }
    }

@pytest.fixture
def mock_pending_response():
    """Mock pending API response."""
    return {
        "output": {
            "task_id": "test-task-123",
            "task_status": "PENDING"
        }
    }

@pytest.fixture
def mock_failed_response():
    """Mock failed API response."""
    return {
        "output": {
            "task_id": "test-task-123",
            "task_status": "FAILED"
        }
    }