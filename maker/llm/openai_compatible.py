from __future__ import annotations
from typing import Any, Mapping, Optional
from maker.llm.base import LLMClient
from maker.llm.http_json import post_json
from maker.types import RawResponse

class OpenAICompatibleClient(LLMClient):
    def __init__(self, *, base_url: str, api_key: str | None = None, timeout: int = 120, extra_headers: Optional[Mapping[str, str]] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.extra_headers = dict(extra_headers or {})

    async def sample(
        self,
        *,
        system: str,
        user: str,
        model: str,
        temperature: float,
        max_tokens: int,
        meta: Optional[Mapping[str, Any]] = None,
    ) -> RawResponse:
        headers = {"Content-Type": "application/json", **self.extra_headers}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = await post_json(f"{self.base_url}/v1/chat/completions", payload, headers, timeout=self.timeout)
        text = data["choices"][0]["message"]["content"]
        return RawResponse(text=text, model=model, temperature=temperature, max_tokens=max_tokens, meta=meta)
