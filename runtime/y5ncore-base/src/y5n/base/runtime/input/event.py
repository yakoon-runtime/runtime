from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .context import InputContext


@dataclass(frozen=True, slots=True)
class InputEvent:
    data: Any
    tokens: list[str] | None = None
    context: InputContext | None = None
    batch_id: str | None = None

    payload: object | None = None

    @classmethod
    def from_raw(cls, data: Any, context=None, batch_id=None):
        return cls(data, [], context, batch_id)

    def update(
        self,
        *,
        data: str | None = None,
        tokens: list[str] | None = None,
    ) -> InputEvent:

        return replace(
            self,
            data=data if data is not None else self.data,
            tokens=tokens if tokens is not None else self.tokens,
        )
