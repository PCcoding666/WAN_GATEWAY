import requests_mock

from src.config import Config
from src.history import HistoryEntry, HistoryStore
from src.wan_client import WanClient


def _client():
    return WanClient(api_key="k", base_url="https://dashscope.example.com")


class TestWanClient:
    def test_endpoints(self):
        c = _client()
        assert c.synthesis_url("wan3.0-video").endswith("/video-generation/video-synthesis")
        assert c.synthesis_url("wan2.2-kf2v-flash").endswith("/image2video/video-synthesis")
        assert c.task_url("t1") == "https://dashscope.example.com/api/v1/tasks/t1"

    def test_submit_ok(self):
        c = _client()
        with requests_mock.Mocker() as m:
            m.post(c.synthesis_url("wan3.0-video"), json={"output": {"task_id": "abc"}})
            assert c.submit({"model": "wan3.0-video"}) == "abc"
            req = m.request_history[0]
            assert req.headers["X-DashScope-Async"] == "enable"
            assert req.headers["Authorization"] == "Bearer k"

    def test_submit_error(self):
        c = _client()
        with requests_mock.Mocker() as m:
            m.post(c.synthesis_url("wan3.0-video"), status_code=400,
                   json={"code": "InvalidParameter", "message": "duration out of range"})
            try:
                c.submit({"model": "wan3.0-video"})
            except Exception as exc:  # WanAPIError
                assert "InvalidParameter" in str(exc)
                assert getattr(exc, "code") == "InvalidParameter"
            else:
                raise AssertionError("expected WanAPIError")

    def test_status_variants(self):
        c = _client()
        with requests_mock.Mocker() as m:
            m.get(c.task_url("t"), [
                {"json": {"output": {"task_status": "RUNNING"}}},
                {"json": {"output": {"task_status": "SUCCEEDED", "video_url": "https://v/x.mp4"},
                          "usage": {"video_duration": 5}}},
                {"json": {"output": {"task_status": "FAILED", "code": "DataInspectionFailed",
                                     "message": "unsafe"}}},
            ])
            s1 = c.status("t")
            assert s1.status == "RUNNING" and not s1.finished
            s2 = c.status("t")
            assert s2.finished and s2.video_url == "https://v/x.mp4" and s2.usage == {"video_duration": 5}
            s3 = c.status("t")
            assert s3.status == "FAILED" and "DataInspectionFailed" in s3.error_message

    def test_download(self, tmp_path):
        c = _client()
        with requests_mock.Mocker() as m:
            m.get("https://v/x.mp4", content=b"vid")
            local = c.download("https://v/x.mp4", "task9", dest_dir=str(tmp_path))
        assert local and local.endswith("task9.mp4")
        assert open(local, "rb").read() == b"vid"


class TestHistory:
    def test_roundtrip(self, tmp_path):
        path = str(tmp_path / "h.json")
        h = HistoryStore(path=path, limit=3)
        for i in range(5):
            h.add(HistoryEntry(task_id=f"t{i}", model="wan3.0-video", task="t2v", prompt="p" * 100,
                               created_at=i))
        assert [e.task_id for e in h.recent()] == ["t4", "t3", "t2"]
        h.update("t4", status="SUCCEEDED", video_url="u")
        h2 = HistoryStore(path=path, limit=3)
        assert h2.get("t4").status == "SUCCEEDED"
        rows = h2.as_rows()
        assert rows[0][1].endswith("SUCCEEDED") and rows[0][5] == "t4"
        assert rows[0][4].endswith("…")
