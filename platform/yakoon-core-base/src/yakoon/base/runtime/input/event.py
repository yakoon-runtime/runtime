from __future__ import annotations

from dataclasses import dataclass, replace

from .context import InputContext


@dataclass(frozen=True, slots=True)
class InputEvent:
    command: str
    tokens: list[str] | None = None
    context: InputContext | None = None
    batch_id: str | None = None

    payload: object | None = None

    @classmethod
    def from_raw(cls, raw: str, context=None, batch_id=None):
        return cls(raw.strip(), [], context, batch_id)

    def with_tokens(
        self,
        tokens: list[str],
    ) -> InputEvent:

        return replace(
            self,
            tokens=tokens,
        )
