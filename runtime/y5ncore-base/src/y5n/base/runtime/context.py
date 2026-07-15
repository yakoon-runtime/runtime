from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class CommandContext:
    """Language-neutral command context.

    The runtime builds this from its internal objects and makes it
    available to the executor. The executor passes it to the command.
    The SDK wraps it into language-native objects.

    Fields are simple types (str, dict) so this can be serialized
    to JSON for non-Python executors.
    """

    path: str | None = None
    request: dict | None = None
    session: dict | None = None
    ports: dict | None = None

    def __getitem__(self, key: str):
        return getattr(self, key)


_context_var: ContextVar[CommandContext] = ContextVar("y5n_command_context")


def _set_context(ctx: CommandContext) -> None:
    _context_var.set(ctx)


class _Context:
    """Entry point for accessing the runtime context.

    Usage:
        ctx = context.current()
        print(ctx["request"])
    """

    @staticmethod
    def current() -> CommandContext:
        try:
            return _context_var.get()
        except LookupError:
            return CommandContext()


context = _Context()
