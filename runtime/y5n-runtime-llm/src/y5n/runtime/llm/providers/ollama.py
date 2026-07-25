from __future__ import annotations

import httpx
from y5n.runtime.api.llm import LLMRequest, LLMResponse


class OllamaProvider:

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def complete(self, request: LLMRequest) -> LLMResponse:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": m.role, "content": m.content} for m in request.messages
                    ],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return LLMResponse(text=resp.json()["message"]["content"])
