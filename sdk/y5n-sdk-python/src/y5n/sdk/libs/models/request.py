"""Request — parse tokens into args and options.

Mirrors the runtime's Request API as a local SDK model.
"""

from __future__ import annotations

from y5n.runtime.api.tokens import TokenQuery


class Request(TokenQuery):
    """Parse and query command-line tokens.

    Conventions:
        - First token is the command name.
        - Options follow ``--name value``.
        - Flags are options without a value.
        - Positional arguments exclude option keys and option values.
    """

    def __init__(self, command: str, tokens: list[str] | None = None) -> None:
        super().__init__(tokens)
        self._command: str = command

    @classmethod
    def from_tokens(cls, tokens: list[str] | None = None) -> Request:
        tokens = tokens or []
        cmd = tokens[0] if tokens else ""
        return cls(command=cmd, tokens=tokens[1:] if len(tokens) > 1 else [])

    @property
    def command(self) -> str:
        return self._command
