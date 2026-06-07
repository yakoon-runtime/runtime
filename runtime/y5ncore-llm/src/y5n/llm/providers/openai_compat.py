from __future__ import annotations

import httpx

from y5n.base.llm import LLMRequest, LLMResponse


class OpenAICompatibleProvider:

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        model: str = "deepseek-coder",
        api_key: str = "",
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key

    async def complete(self, request: LLMRequest) -> LLMResponse:
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
            resp.raise_for_status()
            return LLMResponse(
                text=resp.json()["choices"][0]["message"]["content"]
            )

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self._api_key:
            h["Authorization"] = f"Bearer {self._api_key}"
        return h
