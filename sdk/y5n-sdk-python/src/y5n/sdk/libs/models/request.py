"""Request — a convenience view over the invocation.

Mirrors the runtime's Request API as a local SDK model. The command is the
node path (already known); ``tokens`` are the invocation arguments. The
Request is a view — the canonical data lives in the context
(``node.path`` + ``args``).
"""

from __future__ import annotations

from y5n.runtime.api.tokens import TokenQuery


class Request(TokenQuery):
    """Parse and query invocation arguments.

    Conventions:
        - The command is provided separately (from the context node path).
        - Options follow ``--name value``.
        - Flags are options without a value.
        - Positional arguments exclude option keys and option values.
    """

    def __init__(self, command: str, tokens: list[str] | None = None) -> None:
        super().__init__(tokens)
        self._command: str = command

    @property
    def command(self) -> str:
        return self._command
