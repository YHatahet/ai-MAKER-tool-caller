from maker.llm.base import LLMClient
from maker.llm.http_json import post_json
from maker.types import RawResponse


class NebiusClient(LLMClient):
    def __init__(self, base_url, api_key, timeout=120):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def sample(self, *, system, user, model, temperature, max_tokens, meta=None):

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": [{"type": "text", "text": user}]},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = await post_json(
            f"{self.base_url}/v1/chat/completions",
            payload,
            headers,
            timeout=self.timeout,
        )

        text = data["choices"][0]["message"]["content"]

        return RawResponse(
            text=text,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            meta=meta,
        )
