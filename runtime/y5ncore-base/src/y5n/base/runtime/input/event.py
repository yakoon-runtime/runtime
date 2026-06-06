from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .context import InputContext


@dataclass(frozen=True, slots=True)
class Event:
    payload: Any
    context: InputContext | None = None

    @classmethod
    def from_raw(cls, data: str, context=None):
        return cls(payload=data, context=context)

    def update(
        self,
        *,
        payload: Any | None = None,
    ) -> Event:

        return replace(
            self,
            payload=payload if payload is not None else self.payload,
        )

