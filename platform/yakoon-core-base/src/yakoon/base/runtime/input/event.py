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

    def update(
        self,
        *,
        command: str | None = None,
        tokens: list[str] | None = None,
    ) -> InputEvent:

        return replace(
            self,
            command=command if command is not None else self.command,
            tokens=tokens if tokens is not None else self.tokens,
        )
