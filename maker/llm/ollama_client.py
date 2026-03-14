from __future__ import annotations
from typing import Any, Mapping, Optional
from maker.llm.base import LLMClient
from maker.llm.http_json import post_json
from maker.types import RawResponse

class OllamaClient(LLMClient):
    def __init__(self, *, base_url: str = "http://localhost:11434", timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

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
        payload = {
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        data = await post_json(f"{self.base_url}/api/chat", payload, {"Content-Type": "application/json"}, timeout=self.timeout)
        text = data["message"]["content"]
        return RawResponse(text=text, model=model, temperature=temperature, max_tokens=max_tokens, meta=meta)
