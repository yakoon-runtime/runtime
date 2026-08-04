from __future__ import annotations

from typing import Any

from y5n.runtime.api.tokens import TokenQuery


class Request(TokenQuery):
    """Parse and query a single command-line style input.

    Tokenization is expected to be done before (e.g. via Event).

    Conventions:
        - Command is provided separately.
        - Tokens represent all arguments.
        - Options follow `--name value`.
        - Flags are options without a value.
        - Positional arguments exclude option keys and option values.

    This class intentionally represents exactly one command.
    """

    def __init__(
        self,
        command: str,
        tokens: list[str] | None,
        payload: Any | None = None,
        lang: str = "",
    ) -> None:
        """Create a Request from normalized input.

        Args:
            command: The command name (already extracted).
            tokens: Tokenized arguments (order preserved).

        Notes:
            Tokens must already be split (e.g. via shlex).
        """
        super().__init__(tokens)
        self._command: str = command
        self.payload = payload
        self.lang = lang

    @classmethod
    def from_tokens(cls, tokens: list[str] | None) -> Request:
        """Create a Request from raw tokens (command name is first token)."""
        tokens = tokens or []
        return cls(
            command=tokens[0] if tokens else "",
            tokens=tokens[1:] if len(tokens) > 1 else [],
            payload=None,
            lang="",
        )

    @property
    def command(self) -> str:
        """The command name (first token), lowercased."""
        return self._command
