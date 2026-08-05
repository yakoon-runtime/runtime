from __future__ import annotations

from typing import Any

from y5n.runtime.api.tokens import TokenQuery


class Request(TokenQuery):
    """Parse and query a single command-style invocation.

    The command is provided separately (it is the node path); ``tokens``
    represent the arguments. Conventions:
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
            command: The command name (the node path).
            tokens: Tokenized arguments (order preserved).

        Notes:
            Tokens must already be split (e.g. via shlex).
        """
        super().__init__(tokens)
        self._command: str = command
        self.payload = payload
        self.lang = lang

    @property
    def command(self) -> str:
        """The command name (the node path), lowercased."""
        return self._command
