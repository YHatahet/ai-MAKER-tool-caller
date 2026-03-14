from __future__ import annotations
import random
from typing import Mapping, Optional, Callable
from maker.llm.base import LLMClient
from maker.types import RawResponse

class MockLLMClient(LLMClient):
    def __init__(self, fn: Callable[..., str], *, seed: int = 0, model_name: str = "mock"):
        self.fn = fn
        self.rng = random.Random(seed)
        self.model_name = model_name

    async def sample(
        self,
        *,
        system: str,
        user: str,
        model: str,
        temperature: float,
        max_tokens: int,
        meta: Optional[Mapping[str, object]] = None,
    ) -> RawResponse:
        local_meta = dict(meta or {})
        local_meta.setdefault("rand", self.rng.random())
        text = self.fn(system=system, user=user, temperature=temperature, max_tokens=max_tokens, meta=local_meta)
        return RawResponse(text=text, model=model or self.model_name, temperature=temperature, max_tokens=max_tokens, meta=local_meta)
