from __future__ import annotations
import asyncio
import json
import urllib.request
import urllib.error
from typing import Any, Mapping

def _sync_post_json(url: str, payload: Mapping[str, Any], headers: Mapping[str, str], timeout: int) -> Any:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=dict(headers), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} for {url}: {err}") from e

def _sync_get_json(url: str, headers: Mapping[str, str], timeout: int) -> Any:
    req = urllib.request.Request(url, headers=dict(headers), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} for {url}: {err}") from e

async def post_json(url: str, payload: Mapping[str, Any], headers: Mapping[str, str], timeout: int = 120) -> Any:
    return await asyncio.to_thread(_sync_post_json, url, payload, headers, timeout)

async def get_json(url: str, headers: Mapping[str, str], timeout: int = 120) -> Any:
    return await asyncio.to_thread(_sync_get_json, url, headers, timeout)
