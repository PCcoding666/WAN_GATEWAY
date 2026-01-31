import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
from PIL import Image
import io

# Add root to the path so we can import src as a package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.keyframe_to_video_service import KeyFrameVideoService, VideoResult
from src.config import Config

class TestKeyFrameVideoService(unittest.TestCase):

    def setUp(self):
        self.api_key = "test_api_key"
        self.service = KeyFrameVideoService(api_key=self.api_key)

        # Patch Config
        self.config_patcher = patch('src.keyframe_to_video_service.Config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.DEFAULT_STYLE = "<auto>"
        self.mock_config.REQUEST_TIMEOUT = 30
        self.mock_config.KEYFRAME_POLLING_INTERVAL = 0.1
        self.mock_config.KEYFRAME_MAX_POLL_TIME = 1
        self.mock_config.MAX_PROMPT_LENGTH = 1000
        self.mock_config.get_keyframe_to_video_models.return_value = ["wanx2.1-kf2v-plus"]
        self.mock_config.validate_image_upload.return_value = None # Valid image

        # Mock oss_service
        self.oss_patcher = patch('src.keyframe_to_video_service.oss_service')
        self.mock_oss = self.oss_patcher.start()

    def tearDown(self):
        self.config_patcher.stop()
        self.oss_patcher.stop()

    def create_dummy_image(self):
        img = Image.new('RGB', (100, 100), color = 'red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        img_byte_arr.size = 1024
        return img_byte_arr

    @patch('requests.post')
    @patch('src.keyframe_to_video_service.KeyFrameVideoService._poll_task_result')
    @patch('src.keyframe_to_video_service.KeyFrameVideoService._download_video_locally')
    def test_generate_video_success(self, mock_download, mock_poll, mock_post):
        # Setup mocks
        self.mock_oss.upload_image.side_effect = [
            ("http://oss.example.com/start.jpg", {"size": 1024}),
            ("http://oss.example.com/end.jpg", {"size": 1024})
        ]

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'output': {'task_id': 'task_123'}
        }

        mock_poll.return_value = "http://example.com/video.mp4"
        mock_download.return_value = "/tmp/video.mp4"

        # Execute
        start_img = self.create_dummy_image()
        end_img = self.create_dummy_image()

        result = self.service.generate_video(
            start_frame_file=start_img,
            end_frame_file=end_img,
            prompt="Transition",
            model="wanx2.1-kf2v-plus"
        )

        # Verify
        self.assertTrue(result.success)
        self.assertEqual(result.video_url, "http://example.com/video.mp4")
        self.assertEqual(result.task_id, "task_123")

        # Verify OSS upload (called twice)
        self.assertEqual(self.mock_oss.upload_image.call_count, 2)

        # Verify API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['input']['first_frame_url'], "http://oss.example.com/start.jpg")
        self.assertEqual(kwargs['json']['input']['last_frame_url'], "http://oss.example.com/end.jpg")
        self.assertEqual(kwargs['json']['input']['prompt'], "Transition")

    def test_validate_inputs_missing_frames(self):
        img = self.create_dummy_image()

        # Missing start frame
        result = self.service.generate_video(start_frame_file=None, end_frame_file=img)
        self.assertFalse(result.success)
        self.assertTrue("Start frame image is required" in result.error_message)

        # Missing end frame
        result = self.service.generate_video(start_frame_file=img, end_frame_file=None)
        self.assertFalse(result.success)
        self.assertTrue("End frame image is required" in result.error_message)

    def test_validate_inputs_invalid_model(self):
        img = self.create_dummy_image()
        result = self.service.generate_video(
            start_frame_file=img,
            end_frame_file=img,
            model="invalid-model"
        )
        self.assertFalse(result.success)
        self.assertTrue("Invalid model" in result.error_message)

    @patch('requests.post')
    def test_upload_failure(self, mock_post):
        # First upload fails
        self.mock_oss.upload_image.side_effect = [(None, None), (None, None)]

        start_img = self.create_dummy_image()
        end_img = self.create_dummy_image()

        result = self.service.generate_video(start_frame_file=start_img, end_frame_file=end_img)

        self.assertFalse(result.success)
        self.assertTrue("Failed to process and upload" in result.error_message)
        mock_post.assert_not_called()

if __name__ == '__main__':
    unittest.main()
