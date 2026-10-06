"""
Minimal check: does Bailian's web-search agent return Xiaohongshu (小红书) sources?

Run:
    DASHSCOPE_API_KEY=sk-xxx pytest tests/integration/test_xhs_search_source.py -s

Modes:
  - BAILIAN_APP_ID set  -> call that Bailian application (agent) with web search
  - otherwise           -> call a Qwen model with enable_search + forced_search

The test scans the full raw JSON response (answer, search_info, doc_references,
thoughts) for Xiaohongshu domains, and prints every URL the search returned.
"""
import json
import os
import re

import pytest
import requests

API_KEY = os.getenv("DASHSCOPE_API_KEY")
APP_ID = os.getenv("BAILIAN_APP_ID")
MODEL = os.getenv("BAILIAN_SEARCH_MODEL", "qwen-plus")
QUERY = os.getenv("XHS_QUERY", "小红书上大家推荐的东京旅游攻略")

XHS_PATTERN = re.compile(r"xiaohongshu\.com|xhslink\.com|小红书", re.I)
URL_PATTERN = re.compile(r"https?://[^\s\"'\\)>\]]+")

pytestmark = pytest.mark.skipif(not API_KEY, reason="DASHSCOPE_API_KEY not set")


def _call_app() -> dict:
    resp = requests.post(
        f"https://dashscope.aliyuncs.com/api/v1/apps/{APP_ID}/completion",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "input": {"prompt": QUERY},
            "parameters": {"has_thoughts": True},
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def _call_model() -> dict:
    resp = requests.post(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": QUERY}],
            "enable_search": True,
            "search_options": {"forced_search": True, "enable_source": True},
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def test_search_returns_xiaohongshu_source():
    data = _call_app() if APP_ID else _call_model()
    raw = json.dumps(data, ensure_ascii=False)

    urls = sorted(set(URL_PATTERN.findall(raw)))
    xhs_hits = [u for u in urls if XHS_PATTERN.search(u)]

    print(f"\nmode={'app' if APP_ID else 'model:' + MODEL}  query={QUERY!r}")
    print(f"{len(urls)} source URLs returned:")
    for u in urls:
        print(("  [XHS] " if u in xhs_hits else "        ") + u)

    assert urls, "search returned no source URLs at all (search may not have triggered)"
    assert xhs_hits, "no Xiaohongshu source found in search results"
