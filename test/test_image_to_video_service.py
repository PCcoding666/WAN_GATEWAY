import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
from PIL import Image
import io

# Add root to the path so we can import src as a package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.image_to_video_service import ImageToVideoService, VideoResult
from src.config import Config

class TestImageToVideoService(unittest.TestCase):

    def setUp(self):
        self.api_key = "test_api_key"
        self.service = ImageToVideoService(api_key=self.api_key)

        # Patch Config
        self.config_patcher = patch('src.image_to_video_service.Config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.DEFAULT_STYLE = "<auto>"
        self.mock_config.DEFAULT_DURATION = 5
        self.mock_config.DEFAULT_AUDIO_ENABLED = True
        self.mock_config.DURATION_OPTIONS = [5, 10]
        self.mock_config.REQUEST_TIMEOUT = 30
        self.mock_config.KEYFRAME_POLLING_INTERVAL = 0.1
        self.mock_config.KEYFRAME_MAX_POLL_TIME = 1
        self.mock_config.get_image_to_video_models.return_value = ["wan2.5-i2v-preview"]
        self.mock_config.get_max_prompt_length.return_value = 1000
        self.mock_config.get_supported_resolutions_for_model.return_value = ["1080P"]
        self.mock_config.supports_audio.return_value = True
        self.mock_config.validate_image_upload.return_value = None # Valid image

        # Mock oss_service
        self.oss_patcher = patch('src.image_to_video_service.oss_service')
        self.mock_oss = self.oss_patcher.start()

    def tearDown(self):
        self.config_patcher.stop()
        self.oss_patcher.stop()

    def create_dummy_image(self):
        img = Image.new('RGB', (100, 100), color = 'red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        # Mock file-like object attributes
        img_byte_arr.size = 1024 # Fake size
        return img_byte_arr

    @patch('requests.post')
    @patch('src.image_to_video_service.ImageToVideoService._poll_task_result')
    @patch('src.image_to_video_service.ImageToVideoService._download_video_locally')
    def test_generate_video_success(self, mock_download, mock_poll, mock_post):
        # Setup mocks
        self.mock_oss.upload_image.return_value = ("http://oss.example.com/image.jpg", {"size": 1024})

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'output': {'task_id': 'task_123'}
        }

        mock_poll.return_value = "http://example.com/video.mp4"
        mock_download.return_value = "/tmp/video.mp4"

        # Execute
        image_file = self.create_dummy_image()
        result = self.service.generate_video(
            image_file=image_file,
            prompt="A moving cat",
            model="wan2.5-i2v-preview"
        )

        # Verify
        self.assertTrue(result.success)
        self.assertEqual(result.video_url, "http://example.com/video.mp4")
        self.assertEqual(result.task_id, "task_123")

        # Verify OSS upload
        self.mock_oss.upload_image.assert_called_once()

        # Verify API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['input']['img_url'], "http://oss.example.com/image.jpg")
        self.assertEqual(kwargs['json']['input']['prompt'], "A moving cat")

    def test_validate_inputs_no_image(self):
        result = self.service.generate_video(image_file=None)
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Image file is required")

    def test_validate_inputs_invalid_model(self):
        image_file = self.create_dummy_image()
        result = self.service.generate_video(image_file=image_file, model="invalid-model")
        self.assertFalse(result.success)
        self.assertTrue("Invalid model" in result.error_message)

    @patch('requests.post')
    def test_upload_failure(self, mock_post):
        self.mock_oss.upload_image.return_value = (None, None)

        image_file = self.create_dummy_image()
        result = self.service.generate_video(image_file=image_file)

        self.assertFalse(result.success)
        self.assertTrue("Failed to process and upload image" in result.error_message)
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_submit_task_failure(self, mock_post):
        self.mock_oss.upload_image.return_value = ("http://oss.example.com/image.jpg", {})

        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {"message": "Bad Request"}

        image_file = self.create_dummy_image()
        result = self.service.generate_video(image_file=image_file)

        self.assertFalse(result.success)
        self.assertTrue("Bad Request" in result.error_message)

if __name__ == '__main__':
    unittest.main()
