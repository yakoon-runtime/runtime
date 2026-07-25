"""Request — parse tokens into args and options.

Mirrors the runtime's Request API as a local SDK model.
"""

from __future__ import annotations

from typing import Any


class Request:
    """Parse and query command-line tokens.

    Conventions:
        - First token is the command name.
        - Options follow ``--name value``.
        - Flags are options without a value.
        - Positional arguments exclude option keys and option values.
    """

    def __init__(self, command: str, tokens: list[str] | None = None) -> None:
        self._command: str = command
        self._args: list[str] = tokens or []

    @classmethod
    def from_tokens(cls, tokens: list[str] | None = None) -> Request:
        tokens = tokens or []
        cmd = tokens[0] if tokens else ""
        return cls(command=cmd, tokens=tokens[1:] if len(tokens) > 1 else [])

    @property
    def command(self) -> str:
        return self._command

    def args(self) -> list[str]:
        return list(self._args)

    def token(self, index: int, default: Any = None) -> Any:
        try:
            return self._args[index]
        except IndexError:
            return default

    def arg(self, index: int, default: Any = None) -> Any:
        pos = self._pos_args()
        try:
            return pos[index]
        except IndexError:
            return default

    def has_args(self) -> bool:
        return bool(self._args)

    def arg_count(self) -> int:
        return len(self._args)

    def has_option(self, name: str) -> bool:
        return f"--{name}" in self._args

    def option(self, name: str, default: Any = None) -> Any:
        key = f"--{name}"
        try:
            idx = self._args.index(key)
        except ValueError:
            return default

        if idx + 1 >= len(self._args):
            return default

        value = self._args[idx + 1]
        if value.startswith("--"):
            return default

        return value

    def _pos_args(self) -> list[str]:
        out: list[str] = []
        i = 0
        while i < len(self._args):
            tok = self._args[i]
            if tok.startswith("--"):
                i += 1
                if i < len(self._args) and not self._args[i].startswith("--"):
                    i += 1
                continue
            out.append(tok)
            i += 1
        return out
