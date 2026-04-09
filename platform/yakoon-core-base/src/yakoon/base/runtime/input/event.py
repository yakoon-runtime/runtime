from __future__ import annotations

import shlex
from dataclasses import dataclass

from .context import InputContext


@dataclass(frozen=True, slots=True)
class InputEvent:
    command: str
    tokens: list[str]
    context: InputContext | None = None
    batch_id: str | None = None

    @classmethod
    def from_raw(cls, raw: str, context=None, batch_id=None):
        parts = shlex.split(raw, posix=True)
        if not parts:
            return cls("", [], context, batch_id)

        return cls(parts[0].lower(), parts[1:], context, batch_id)

    @classmethod
    def from_tokens(cls, command: str, tokens: list[str], context=None, batch_id=None):
        return cls(command, tokens, context, batch_id)
