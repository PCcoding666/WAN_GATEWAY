"""
Tiny JSON-backed task history so a browser refresh (or a restart) never loses
a task id.  DashScope task ids and video URLs stay valid for 24 h, so anything
in here can be resumed from the UI or the CLI.
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .config import Config


@dataclass
class HistoryEntry:
    task_id: str
    model: str
    task: str
    prompt: str = ""
    status: str = "PENDING"
    created_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    video_url: Optional[str] = None
    local_path: Optional[str] = None
    error: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    @property
    def elapsed(self) -> float:
        end = self.finished_at or time.time()
        return end - self.created_at


class HistoryStore:
    def __init__(self, path: Optional[str] = None, limit: Optional[int] = None):
        self.path = path or Config.HISTORY_FILE
        self.limit = limit or Config.HISTORY_LIMIT
        self._lock = threading.Lock()
        self._entries: Dict[str, HistoryEntry] = {}
        self._load()

    # ------------------------------------------------------------ storage
    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                for raw in json.load(fh):
                    raw = {k: v for k, v in raw.items() if k in HistoryEntry.__dataclass_fields__}
                    e = HistoryEntry(**raw)
                    self._entries[e.task_id] = e
        except (OSError, ValueError, TypeError):
            self._entries = {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump([asdict(e) for e in self.recent(self.limit)], fh, ensure_ascii=False, indent=1)
        os.replace(tmp, self.path)

    # ---------------------------------------------------------------- api
    def add(self, entry: HistoryEntry) -> HistoryEntry:
        with self._lock:
            self._entries[entry.task_id] = entry
            self._trim()
            self._save()
        return entry

    def update(self, task_id: str, **changes: Any) -> Optional[HistoryEntry]:
        with self._lock:
            e = self._entries.get(task_id)
            if not e:
                return None
            for k, v in changes.items():
                setattr(e, k, v)
            self._save()
            return e

    def get(self, task_id: str) -> Optional[HistoryEntry]:
        return self._entries.get(task_id)

    def recent(self, n: int = 20) -> List[HistoryEntry]:
        return sorted(self._entries.values(), key=lambda e: e.created_at, reverse=True)[:n]

    def pending(self) -> List[HistoryEntry]:
        return [e for e in self._entries.values() if e.status in ("PENDING", "RUNNING")]

    def _trim(self) -> None:
        if len(self._entries) <= self.limit:
            return
        for e in sorted(self._entries.values(), key=lambda e: e.created_at)[: len(self._entries) - self.limit]:
            self._entries.pop(e.task_id, None)

    # ------------------------------------------------------------ display
    def as_rows(self, n: int = 20) -> List[List[str]]:
        rows = []
        for e in self.recent(n):
            icon = {"SUCCEEDED": "✅", "FAILED": "❌", "CANCELED": "⛔",
                    "RUNNING": "⏳", "PENDING": "🕐"}.get(e.status, "❔")
            rows.append([
                time.strftime("%m-%d %H:%M", time.localtime(e.created_at)),
                f"{icon} {e.status}",
                e.task,
                e.model,
                (e.prompt or "")[:60] + ("…" if len(e.prompt or "") > 60 else ""),
                e.task_id,
            ])
        return rows


_default_store: Optional[HistoryStore] = None


def history() -> HistoryStore:
    global _default_store
    if _default_store is None:
        _default_store = HistoryStore()
    return _default_store
