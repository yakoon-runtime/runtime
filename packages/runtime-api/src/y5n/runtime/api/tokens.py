"""Shared token-query logic for command-style inputs.

Request, DataRequest, and the SDK's local Request all parse a token list
into options and positional arguments with identical rules:
- options follow ``--name value``
- flags are options without a value
- positional arguments exclude option keys and option values
"""

from __future__ import annotations

from typing import Any


class TokenQuery:
    """Query a token list for positional arguments and options."""

    def __init__(self, tokens: list[str] | None = None) -> None:
        self._args: list[str] = tokens or []

    def args(self) -> list[str]:
        """All argument tokens (everything after the command token)."""
        return self._args

    def token(self, index: int, default: Any = None) -> Any:
        """Return the Nth argument token (0-based) or a default."""
        try:
            return self._args[index]
        except IndexError:
            return default

    def arg(self, index: int, default: Any = None) -> Any:
        """Return the Nth positional argument (0-based) or a default.

        Positional arguments exclude option keys (``--name``) and their
        values.
        """
        pos = self._pos_args()
        try:
            return pos[index]
        except IndexError:
            return default

    def has_args(self) -> bool:
        """Whether there are any argument tokens."""
        return bool(self._args)

    def arg_count(self) -> int:
        """Number of argument tokens."""
        return len(self._args)

    def has_option(self, name: str) -> bool:
        """Check whether an option key ``--name`` is present (flag or key-value)."""
        return f"--{name}" in self._args

    def option(self, name: str, default: Any = None) -> Any:
        """Return the value for an option of the form ``--name value``.

        Returns the default if the option is missing, has no value, or the
        following token is itself another option (flag).
        """
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
        """Compute positional arguments by skipping options and option values."""
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
