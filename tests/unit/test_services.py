import pytest
from unittest.mock import MagicMock, patch
from src.text_to_video_service import TextToVideoService
from src.config import Config

class TestTextToVideoService:
    @pytest.fixture
    def service(self, mock_env_vars):
        return TextToVideoService(api_key="test_key")

    def test_init(self, service):
        """Test service initialization."""
        assert service.api_key == "test_key"
        assert service.base_url == Config.TEXT_TO_VIDEO_ENDPOINT

    def test_validate_inputs_valid(self, service):
        """Test input validation with valid inputs."""
        error = service._validate_inputs(
            prompt="A test video",
            style="Cinematic",
            aspect_ratio="16:9",
            model="wan2.2-t2v-plus"
        )
        assert error is None

    def test_validate_inputs_empty_prompt(self, service):
        """Test input validation with empty prompt."""
        error = service._validate_inputs(
            prompt="",
            style="Cinematic",
            aspect_ratio="16:9",
            model="wan2.2-t2v-plus"
        )
        assert error == "Prompt cannot be empty"

    def test_validate_inputs_invalid_style(self, service):
        """Test input validation with invalid style."""
        error = service._validate_inputs(
            prompt="Test",
            style="InvalidStyle",
            aspect_ratio="16:9",
            model="wan2.2-t2v-plus"
        )
        assert "Invalid style" in error

    def test_build_request_wan25(self, service):
        """Test request building for Wan 2.5 model."""
        request = service._build_request(
            prompt="Test prompt",
            style="Cinematic",
            aspect_ratio="16:9",
            model="wan2.5-t2v-preview",
            duration=10,
            audio_enabled=True
        )
        
        assert request["model"] == "wan2.5-t2v-preview"
        assert request["input"]["prompt"] == "Test prompt"
        assert request["parameters"]["resolution"] == "1080P"  # Default for Wan 2.5
        assert request["parameters"]["duration"] == 10
        assert request["parameters"]["audio"] is True

    @patch('requests.post')
    def test_submit_task_success(self, mock_post, service):
        """Test successful task submission."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"task_id": "task_123"}
        }
        mock_post.return_value = mock_response

        result = service._submit_task({})
        
        assert result["success"] is True
        assert result["task_id"] == "task_123"

    @patch('requests.post')
    def test_submit_task_failure(self, mock_post, service):
        """Test failed task submission."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "message": "Invalid parameter"
        }
        mock_post.return_value = mock_response

        result = service._submit_task({})
        
        assert result["success"] is False
        assert "Invalid parameter" in result["error"]
