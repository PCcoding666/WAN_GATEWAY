"""
Unit tests for the TextToVideoService class.
"""
import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
import time

from src.text_to_video_service import TextToVideoService, VideoResult
from src.config import Config

class TestTextToVideoService:
    """Test cases for TextToVideoService."""
    
    def test_init_with_api_key(self, mock_api_key):
        """Test service initialization with API key."""
        service = TextToVideoService(api_key=mock_api_key)
        assert service.api_key == mock_api_key
        assert service.base_url == Config.API_ENDPOINT
    
    def test_init_without_api_key_raises_error(self):
        """Test that initialization without API key raises ValueError."""
        with patch.object(Config, 'DASHSCOPE_API_KEY', None):
            with pytest.raises(ValueError, match="API key is required"):
                TextToVideoService()
    
    def test_validate_inputs_empty_prompt(self, service):
        """Test validation with empty prompt."""
        error = service._validate_inputs("", "Cinematic", "16:9")
        assert error == "Prompt cannot be empty"
    
    def test_validate_inputs_whitespace_prompt(self, service):
        """Test validation with whitespace-only prompt."""
        error = service._validate_inputs("   ", "Cinematic", "16:9")
        assert error == "Prompt cannot be empty"
    
    def test_validate_inputs_long_prompt(self, service):
        """Test validation with overly long prompt."""
        long_prompt = "A" * (Config.MAX_PROMPT_LENGTH + 1)
        error = service._validate_inputs(long_prompt, "Cinematic", "16:9")
        assert "Prompt too long" in error
    
    def test_validate_inputs_invalid_style(self, service):
        """Test validation with invalid style."""
        error = service._validate_inputs("Valid prompt", "InvalidStyle", "16:9")
        assert "Invalid style" in error
    
    def test_validate_inputs_invalid_aspect_ratio(self, service):
        """Test validation with invalid aspect ratio."""
        error = service._validate_inputs("Valid prompt", "Cinematic", "invalid:ratio")
        assert "Invalid aspect ratio" in error
    
    def test_validate_inputs_valid(self, service, valid_prompt):
        """Test validation with valid inputs."""
        error = service._validate_inputs(valid_prompt, "Cinematic", "16:9")
        assert error is None
    
    def test_build_request_basic(self, service):
        """Test basic request building."""
        request_data = service._build_request(
            prompt="Test prompt",
            style="Cinematic",
            aspect_ratio="16:9"
        )
        
        expected = {
            "model": "wanx-v1",
            "input": {
                "text": "Test prompt",
                "style": "Cinematic",
                "aspect_ratio": "16:9"
            },
            "parameters": {}
        }
        
        assert request_data == expected
    
    def test_build_request_with_optional_params(self, service):
        """Test request building with optional parameters."""
        request_data = service._build_request(
            prompt="Test prompt",
            style="Cinematic",
            aspect_ratio="16:9",
            negative_prompt="blurry",
            seed=42
        )
        
        assert request_data["parameters"]["negative_prompt"] == "blurry"
        assert request_data["parameters"]["seed"] == 42
    
    def test_build_request_empty_negative_prompt(self, service):
        """Test request building with empty negative prompt."""
        request_data = service._build_request(
            prompt="Test prompt",
            style="Cinematic",
            aspect_ratio="16:9",
            negative_prompt="   ",
            seed=None
        )
        
        # Empty negative prompt should not be included
        assert "negative_prompt" not in request_data["parameters"]
        assert "seed" not in request_data["parameters"]
    
    @patch('src.text_to_video_service.requests.post')
    def test_submit_task_success(self, mock_post, service):
        """Test successful task submission."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"task_id": "test-task-123"}
        }
        mock_post.return_value = mock_response
        
        request_data = {"test": "data"}
        result = service._submit_task(request_data)
        
        assert result["success"] is True
        assert result["task_id"] == "test-task-123"
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"] == request_data
        assert "Authorization" in call_args[1]["headers"]
    
    @patch('src.text_to_video_service.requests.post')
    def test_submit_task_api_error(self, mock_post, service):
        """Test task submission with API error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Invalid request"}
        mock_post.return_value = mock_response
        
        request_data = {"test": "data"}
        result = service._submit_task(request_data)
        
        assert result["success"] is False
        assert "Invalid request" in result["error"]
    
    @patch('src.text_to_video_service.requests.post')
    def test_submit_task_timeout(self, mock_post, service):
        """Test task submission with timeout."""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        request_data = {"test": "data"}
        result = service._submit_task(request_data)
        
        assert result["success"] is False
        assert "timeout" in result["error"].lower()
    
    @patch('src.text_to_video_service.requests.post')
    def test_submit_task_connection_error(self, mock_post, service):
        """Test task submission with connection error."""
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        request_data = {"test": "data"}
        result = service._submit_task(request_data)
        
        assert result["success"] is False
        assert "connection error" in result["error"].lower()
    
    @patch('src.text_to_video_service.requests.get')
    @patch('src.text_to_video_service.time.sleep')
    def test_poll_task_result_success(self, mock_sleep, mock_get, service):
        """Test successful task result polling."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "task_status": "SUCCEEDED",
                "video_url": "https://example.com/video.mp4"
            }
        }
        mock_get.return_value = mock_response
        
        result = service._poll_task_result("test-task-123")
        
        assert result == "https://example.com/video.mp4"
        mock_get.assert_called_once()
    
    @patch('src.text_to_video_service.requests.get')
    @patch('src.text_to_video_service.time.sleep')
    def test_poll_task_result_failed(self, mock_sleep, mock_get, service):
        """Test polling for failed task."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"task_status": "FAILED"}
        }
        mock_get.return_value = mock_response
        
        result = service._poll_task_result("test-task-123")
        
        assert result is None
    
    @patch('src.text_to_video_service.requests.get')
    @patch('src.text_to_video_service.time.sleep')
    @patch('src.text_to_video_service.time.time')
    def test_poll_task_result_timeout(self, mock_time, mock_sleep, mock_get, service):
        """Test polling timeout."""
        # Mock time to simulate timeout - provide more values than needed
        mock_time.side_effect = [0, Config.MAX_POLL_TIME + 1] + [Config.MAX_POLL_TIME + 1] * 10
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"task_status": "PENDING"}
        }
        mock_get.return_value = mock_response
        
        result = service._poll_task_result("test-task-123")
        
        assert result is None
    
    @patch('src.text_to_video_service.requests.get')
    @patch('src.text_to_video_service.time.sleep')
    def test_poll_task_result_pending_then_success(self, mock_sleep, mock_get, service):
        """Test polling with pending then success status."""
        # First call returns PENDING, second returns SUCCEEDED
        responses = [
            Mock(status_code=200, json=lambda: {"output": {"task_status": "PENDING"}}),
            Mock(status_code=200, json=lambda: {
                "output": {
                    "task_status": "SUCCEEDED",
                    "video_url": "https://example.com/video.mp4"
                }
            })
        ]
        mock_get.side_effect = responses
        
        result = service._poll_task_result("test-task-123")
        
        assert result == "https://example.com/video.mp4"
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(Config.POLLING_INTERVAL)
    
    def test_generate_video_validation_error(self, service):
        """Test video generation with validation error."""
        result = service.generate_video("")
        
        assert result.success is False
        assert "empty" in result.error_message.lower()
        assert result.video_url is None
    
    @patch.object(TextToVideoService, '_submit_task')
    def test_generate_video_submission_error(self, mock_submit, service, valid_prompt):
        """Test video generation with submission error."""
        mock_submit.return_value = {
            'success': False,
            'error': 'API error'
        }
        
        result = service.generate_video(valid_prompt)
        
        assert result.success is False
        assert 'API error' in result.error_message
    
    @patch.object(TextToVideoService, '_poll_task_result')
    @patch.object(TextToVideoService, '_submit_task')
    def test_generate_video_success(self, mock_submit, mock_poll, service, valid_prompt):
        """Test successful video generation."""
        mock_submit.return_value = {
            'success': True,
            'task_id': 'test-task-123'
        }
        mock_poll.return_value = 'https://example.com/video.mp4'
        
        result = service.generate_video(valid_prompt)
        
        assert result.success is True
        assert result.video_url == 'https://example.com/video.mp4'
        assert result.task_id == 'test-task-123'
        assert result.generation_time is not None
    
    @patch.object(TextToVideoService, '_poll_task_result')
    @patch.object(TextToVideoService, '_submit_task')
    def test_generate_video_polling_failure(self, mock_submit, mock_poll, service, valid_prompt):
        """Test video generation with polling failure."""
        mock_submit.return_value = {
            'success': True,
            'task_id': 'test-task-123'
        }
        mock_poll.return_value = None  # Polling failed
        
        result = service.generate_video(valid_prompt)
        
        assert result.success is False
        assert 'failed or timed out' in result.error_message
        assert result.task_id == 'test-task-123'
    
    def test_get_service_status(self, service):
        """Test service status retrieval."""
        status = service.get_service_status()
        
        expected_keys = [
            'api_configured', 'api_endpoint', 'max_poll_time',
            'polling_interval', 'supported_styles', 'supported_ratios'
        ]
        
        for key in expected_keys:
            assert key in status
        
        assert isinstance(status['api_configured'], bool)
        assert isinstance(status['supported_styles'], list)
        assert isinstance(status['supported_ratios'], list)
    
    @patch.object(TextToVideoService, '_submit_task')
    def test_generate_video_exception_handling(self, mock_submit, service, valid_prompt):
        """Test exception handling in video generation."""
        mock_submit.side_effect = Exception("Unexpected error")
        
        result = service.generate_video(valid_prompt)
        
        assert result.success is False
        assert "Unexpected error" in result.error_message