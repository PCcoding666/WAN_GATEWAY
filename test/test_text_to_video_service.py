import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add root to the path so we can import src as a package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.text_to_video_service import TextToVideoService, VideoResult
from src.config import Config

class TestTextToVideoService(unittest.TestCase):

    def setUp(self):
        self.api_key = "test_api_key"
        self.service = TextToVideoService(api_key=self.api_key)

        # Patch Config to have predictable values
        self.config_patcher = patch('src.text_to_video_service.Config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.DEFAULT_STYLE = "<auto>"
        self.mock_config.DEFAULT_ASPECT_RATIO = "16:9"
        self.mock_config.DEFAULT_MODEL = "wan2.5-t2v-preview"
        self.mock_config.DEFAULT_DURATION = 5
        self.mock_config.DEFAULT_AUDIO_ENABLED = True
        self.mock_config.STYLE_OPTIONS = ["<auto>", "Cinematic"]
        self.mock_config.ASPECT_RATIO_OPTIONS = ["16:9", "1:1"]
        self.mock_config.DURATION_OPTIONS = [5, 10]
        self.mock_config.REQUEST_TIMEOUT = 30
        self.mock_config.POLLING_INTERVAL = 0.1 # Fast polling for tests
        self.mock_config.MAX_POLL_TIME = 1

        # Setup model options for validation
        self.mock_config.get_text_to_video_models.return_value = ["wan2.5-t2v-preview"]
        self.mock_config.get_max_prompt_length.return_value = 1000
        self.mock_config.get_supported_resolutions_for_model.return_value = ["1080P"]
        self.mock_config.uses_resolution_label.return_value = True
        self.mock_config.supports_audio.return_value = True

    def tearDown(self):
        self.config_patcher.stop()

    @patch('requests.post')
    @patch('src.text_to_video_service.TextToVideoService._poll_task_result')
    @patch('src.text_to_video_service.TextToVideoService._download_video_locally')
    def test_generate_video_success(self, mock_download, mock_poll, mock_post):
        # Setup mocks
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'output': {'task_id': 'task_123'}
        }

        mock_poll.return_value = "http://example.com/video.mp4"
        mock_download.return_value = "/tmp/video.mp4"

        # Execute
        result = self.service.generate_video(
            prompt="A cute cat",
            style="Cinematic",
            aspect_ratio="16:9",
            model="wan2.5-t2v-preview"
        )

        # Verify
        self.assertTrue(result.success)
        self.assertEqual(result.video_url, "http://example.com/video.mp4")
        self.assertEqual(result.local_video_path, "/tmp/video.mp4")
        self.assertEqual(result.task_id, "task_123")

        # Verify API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['input']['prompt'], "A cute cat")
        self.assertEqual(kwargs['json']['parameters']['resolution'], "1080P")

    def test_validate_inputs_empty_prompt(self):
        result = self.service.generate_video(prompt="")
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Prompt cannot be empty")

    def test_validate_inputs_invalid_style(self):
        result = self.service.generate_video(prompt="test", style="InvalidStyle")
        self.assertFalse(result.success)
        self.assertTrue("Invalid style" in result.error_message)

    def test_validate_inputs_invalid_model(self):
        self.mock_config.get_text_to_video_models.return_value = ["wan2.5-t2v-preview"]
        result = self.service.generate_video(prompt="test", model="invalid-model")
        self.assertFalse(result.success)
        self.assertTrue("Invalid model" in result.error_message)

    @patch('requests.post')
    def test_submit_task_failure(self, mock_post):
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {"message": "Bad Request"}

        result = self.service.generate_video(prompt="test")

        self.assertFalse(result.success)
        self.assertTrue("Bad Request" in result.error_message)

    @patch('requests.post')
    @patch('src.text_to_video_service.TextToVideoService._poll_task_result')
    def test_generate_video_poll_failure(self, mock_poll, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'output': {'task_id': 'task_123'}
        }

        mock_poll.return_value = None # Polling failed or timed out

        result = self.service.generate_video(prompt="test")

        self.assertFalse(result.success)
        self.assertEqual(result.task_id, "task_123")
        self.assertTrue("Video generation failed or timed out" in result.error_message)

if __name__ == '__main__':
    unittest.main()
