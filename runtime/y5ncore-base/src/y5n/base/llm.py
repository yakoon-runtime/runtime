from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LLMRequest:
    prompt: str


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str


class OnCallLLM(Protocol):
    async def complete(self, request: LLMRequest) -> LLMResponse: ...
