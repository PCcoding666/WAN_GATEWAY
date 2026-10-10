
"""
Thin, model-agnostic DashScope client for Wan video generation.

Three verbs: :meth:`WanClient.submit`, :meth:`WanClient.status`,
:meth:`WanClient.download`, plus :meth:`WanClient.wait` which polls for you and
:meth:`WanClient.cancel` for queued tasks.  All transport details (region host,
auth header, async header, retries) live here and nowhere else.
"""
from __future__ import annotations

import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Config
from .models import KF2V, get_spec

logger = logging.getLogger(__name__)


class WanAPIError(RuntimeError):
    def __init__(self, message: str, code: Optional[str] = None, request_id: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.request_id = request_id


@dataclass
class TaskStatus:
    task_id: str
    status: str                         # PENDING | RUNNING | SUCCEEDED | FAILED | CANCELED | UNKNOWN | ERROR
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def finished(self) -> bool:
        return self.status in ("SUCCEEDED", "FAILED", "CANCELED")

    @property
    def usage(self) -> Dict[str, Any]:
        return self.raw.get("usage") or {}


class WanClient:
    """Submit / poll / download against one DashScope region."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 timeout: int = Config.REQUEST_TIMEOUT):
        self.api_key = api_key or Config.DASHSCOPE_API_KEY
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is not set")
        self.base_url = (base_url or Config.DASHSCOPE_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    # ------------------------------------------------------------ endpoints
    def synthesis_url(self, model_id: Optional[str] = None, task: Optional[str] = None) -> str:
        """Keyframe-legacy models live on ``image2video``; everything else on ``video-generation``."""
        if model_id:
            try:
                spec = get_spec(model_id)
                if spec.dialect == "kf2v" or (task == KF2V and spec.dialect == "kf2v"):
                    return f"{self.base_url}/api/v1/services/aigc/image2video/video-synthesis"
            except ValueError:
                pass
        return f"{self.base_url}/api/v1/services/aigc/video-generation/video-synthesis"

    def task_url(self, task_id: str) -> str:
        return f"{self.base_url}/api/v1/tasks/{task_id}"

    # --------------------------------------------------------------- verbs
    def submit(self, payload: Dict[str, Any], task: Optional[str] = None) -> str:
        """POST the payload asynchronously and return the DashScope ``task_id``."""
        url = self.synthesis_url(payload.get("model"), task)
        logger.info("POST %s model=%s", url, payload.get("model"))
        resp = self._session.post(
            url, json=payload, timeout=self.timeout,
            headers={"X-DashScope-Async": "enable"},
        )
        data = _json_or_text(resp)
        if resp.status_code != 200:
            raise WanAPIError(_error_message(data, resp), code=_get(data, "code"),
                              request_id=_get(data, "request_id"))
        task_id = _get(data, "output", "task_id")
        if not task_id:
            raise WanAPIError(f"No task_id in response: {data}")
        return task_id

    def status(self, task_id: str) -> TaskStatus:
        try:
            resp = self._session.get(self.task_url(task_id), timeout=self.timeout)
        except requests.RequestException as exc:
            return TaskStatus(task_id, "ERROR", error_message=str(exc))
        data = _json_or_text(resp)
        if resp.status_code != 200:
            return TaskStatus(task_id, "ERROR", error_message=_error_message(data, resp), raw=data)
        output = data.get("output") if isinstance(data, dict) else None
        if not isinstance(output, dict):
            return TaskStatus(task_id, "ERROR", error_message=f"Unexpected response: {data}", raw=data)
        st = output.get("task_status", "UNKNOWN")
        video_url = output.get("video_url")
        if not video_url and output.get("results"):
            first = output["results"][0] if isinstance(output["results"], list) else {}
            video_url = first.get("url") or first.get("video_url")
        err = None
        if st == "FAILED":
            err = output.get("message") or output.get("error") or data.get("message") or "Task failed"
            if output.get("code"):
                err = f"{output['code']}: {err}"
        return TaskStatus(task_id, st, video_url=video_url, error_message=err, raw=data)

    def cancel(self, task_id: str) -> bool:
        """Cancel a *queued* (PENDING) task. Running tasks cannot be cancelled."""
        try:
            resp = self._session.post(f"{self.task_url(task_id)}/cancel", timeout=self.timeout)
            return resp.status_code == 200
        except requests.RequestException as exc:
            logger.warning("cancel failed: %s", exc)
            return False

    def wait(self, task_id: str, interval: float = 5.0, max_wait: float = 1800.0,
             on_tick: Optional[Callable[[TaskStatus, float], None]] = None) -> TaskStatus:
        start = time.time()
        while True:
            st = self.status(task_id)
            elapsed = time.time() - start
            if on_tick:
                on_tick(st, elapsed)
            if st.finished:
                return st
            if elapsed > max_wait:
                return TaskStatus(task_id, "ERROR", error_message=f"Timed out after {int(elapsed)}s", raw=st.raw)
            time.sleep(interval)

    def download(self, video_url: str, task_id: str, dest_dir: Optional[str] = None) -> Optional[str]:
        """Download the (24h-expiring) video URL to disk; returns the local path."""
        dest_dir = dest_dir or Config.VIDEO_DIR
        os.makedirs(dest_dir, exist_ok=True)
        ext = os.path.splitext(urlparse(video_url).path)[1] or ".mp4"
        local = os.path.join(dest_dir, f"{task_id}{ext}")
        if os.path.exists(local) and os.path.getsize(local) > 0:
            return local

        sess = requests.Session()
        sess.mount("https://", HTTPAdapter(max_retries=Retry(
            total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])))
        try:
            with sess.get(video_url, stream=True, timeout=(30, 180)) as r:
                if r.status_code != 200:
                    logger.error("download failed HTTP %s", r.status_code)
                    return None
                with open(local, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=1 << 16):
                        if chunk:
                            fh.write(chunk)
        except requests.RequestException as exc:
            logger.error("download error: %s", exc)
            return None
        if os.path.getsize(local) == 0:
            os.unlink(local)
            return None
        return local


# ---------------------------------------------------------------- helpers
def _json_or_text(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except ValueError:
        return {"message": resp.text}


def _get(data: Any, *keys: str) -> Any:
    cur = data
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _error_message(data: Any, resp: requests.Response) -> str:
    if isinstance(data, dict):
        code = data.get("code")
        msg = data.get("message") or data.get("error")
        if code and msg:
            return f"{code}: {msg}"
        if msg:
            return str(msg)
    return f"HTTP {resp.status_code}: {resp.text[:300]}"
