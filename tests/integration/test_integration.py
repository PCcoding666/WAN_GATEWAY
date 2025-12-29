import pytest
import requests_mock
from src.text_to_video_service import TextToVideoService
from src.config import Config

class TestIntegration:
    @pytest.fixture
    def service(self, mock_env_vars):
        return TextToVideoService(api_key="test_key")

    def test_full_generation_flow(self, service):
        """Test full video generation flow with mocked API."""
        with requests_mock.Mocker() as m:
            # 1. Mock Submission
            m.post(Config.TEXT_TO_VIDEO_ENDPOINT, json={
                "output": {"task_id": "task_integration_123"}
            }, status_code=200)

            # 2. Mock Polling (Pending -> Running -> Succeeded)
            poll_url = "https://dashscope.aliyuncs.com/api/v1/tasks/task_integration_123"
            
            # Sequence of responses
            m.get(poll_url, [
                {"json": {"output": {"task_status": "PENDING"}}, "status_code": 200},
                {"json": {"output": {"task_status": "RUNNING"}}, "status_code": 200},
                {"json": {
                    "output": {
                        "task_status": "SUCCEEDED",
                        "video_url": "https://oss.example.com/video.mp4"
                    }
                }, "status_code": 200}
            ])

            # 3. Mock Video Download
            m.get("https://oss.example.com/video.mp4", content=b"fake_video_content", status_code=200)

            # Execute
            # We reduce polling interval for test speed
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(service, 'get_polling_interval', lambda: 0.1)
                
                result = service.generate_video(
                    prompt="Integration test video",
                    model="wan2.5-t2v-preview"
                )

            # Verify
            assert result.success is True
            assert result.task_id == "task_integration_123"
            assert result.video_url == "https://oss.example.com/video.mp4"
            assert result.local_video_path is not None
