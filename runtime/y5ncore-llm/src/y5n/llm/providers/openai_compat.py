from __future__ import annotations

import asyncio

import httpx
from y5n.runtime.engine.llm import LLMRequest, LLMResponse


class OpenAICompatibleProvider:

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        model: str = "deepseek-coder",
        api_key: str = "",
        max_retries: int = 3,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._max_retries = max_retries

    async def complete(self, request: LLMRequest) -> LLMResponse:
        for attempt in range(1 + self._max_retries):
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=self._headers(),
                    json={
                        "model": self._model,
                        "messages": [
                            {"role": m.role, "content": m.content}
                            for m in request.messages
                        ],
                        "stream": False,
                    },
                )

                if resp.status_code == 429 and attempt < self._max_retries:
                    await asyncio.sleep(2**attempt)
                    continue

                resp.raise_for_status()
                return LLMResponse(text=resp.json()["choices"][0]["message"]["content"])

        raise RuntimeError("LLM request failed after max retries")

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self._api_key:
            h["Authorization"] = f"Bearer {self._api_key}"
        return h
