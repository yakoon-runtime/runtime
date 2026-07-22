from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class LLMRequest:
    messages: list[LLMMessage] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str


class OnCallLLM(Protocol):
    async def complete(self, request: LLMRequest) -> LLMResponse: ...
