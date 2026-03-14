from __future__ import annotations
import os
from maker.llm.base import LLMClient
from maker.llm.openai_compatible import OpenAICompatibleClient
from maker.llm.ollama_client import OllamaClient
from maker.llm.nebius_client import NebiusClient


def create_client(provider: str, **kwargs) -> LLMClient:
    provider = provider.lower()
    if provider in {"openai", "openai_compatible", "vllm", "llamacpp", "llama.cpp"}:
        base_url = kwargs.get("base_url") or os.environ.get(
            "OPENAI_BASE_URL", "https://api.openai.com"
        )
        api_key = kwargs.get("api_key") or os.environ.get("OPENAI_API_KEY")
        timeout = int(kwargs.get("timeout", 120))
        return OpenAICompatibleClient(
            base_url=base_url, api_key=api_key, timeout=timeout
        )
    if provider == "ollama":
        base_url = kwargs.get("base_url") or os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        timeout = int(kwargs.get("timeout", 120))
        return OllamaClient(base_url=base_url, timeout=timeout)
    if provider == "nebius":
        base_url = kwargs.get("base_url", "https://api.tokenfactory.nebius.com")
        api_key = kwargs.get("api_key") or os.environ.get("NEBIUS_API_KEY")
        return NebiusClient(base_url=base_url, api_key=api_key)
    raise ValueError(f"Unsupported provider: {provider}")
