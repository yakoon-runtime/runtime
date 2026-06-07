from __future__ import annotations

import os

import google.generativeai as genai

from y5n.base.llm import LLMRequest, LLMResponse


class GeminiProvider:

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        api_key: str | None = None,
    ):
        key = api_key or os.getenv("GEMINI_API_KEY") or ""
        genai.configure(api_key=key)
        self._model = genai.GenerativeModel(model)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        response = await self._model.generate_content_async(request.prompt)
        return LLMResponse(text=response.text)
