from __future__ import annotations
import abc
from typing import Mapping, Optional
from maker.types import RawResponse

class LLMClient(abc.ABC):
    @abc.abstractmethod
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
        raise NotImplementedError
