from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DataRequest:

    query: str
    session: Any = None
    caller_app_id: str | None = None

    _source: str = field(init=False, repr=False)
    _tokens: list[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        parts = shlex.split(self.query)

        if not parts:
            raise ValueError("Empty data request")

        object.__setattr__(self, "_source", parts[0])
        object.__setattr__(self, "_tokens", parts[1:])

    @property
    def source(self) -> str:
        return self._source

    def args(self) -> list[str]:
        return self._tokens

    def token(self, index: int, default: Any = None) -> Any:
        try:
            return self._tokens[index]
        except IndexError:
            return default

    def arg(self, index: int, default: Any = None) -> Any:
        pos = self._pos_args()
        try:
            return pos[index]
        except IndexError:
            return default

    def has_args(self) -> bool:
        return bool(self._tokens)

    def arg_count(self) -> int:
        return len(self._tokens)

    def has_option(self, name: str) -> bool:
        return f"--{name}" in self._tokens

    def option(self, name: str, default: Any = None) -> Any:
        key = f"--{name}"

        try:
            idx = self._tokens.index(key)
        except ValueError:
            return default

        if idx + 1 >= len(self._tokens):
            return default

        value = self._tokens[idx + 1]
        if value.startswith("--"):
            return default

        return value

    def _pos_args(self) -> list[str]:
        out: list[str] = []
        i = 0

        while i < len(self._tokens):
            tok = self._tokens[i]

            if tok.startswith("--"):
                i += 1
                if i < len(self._tokens) and not self._tokens[i].startswith("--"):
                    i += 1
                continue

            out.append(tok)
            i += 1

        return out
