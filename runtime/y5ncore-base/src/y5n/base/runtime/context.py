from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any


@dataclass
class CommandContext:
    """Language-neutral command context.

    The runtime builds this from its internal objects and makes it
    available to the executor. The executor passes it to the command.
    The SDK wraps it into language-native objects.

    Fields are simple types (str, list, dict) so this can be
    serialized to JSON for non-Python executors.
    """

    path: str | None = None
    command: str | None = None
    tokens: list[str] | None = None
    session: dict | None = None

    def __getitem__(self, key: str):
        return getattr(self, key)


_context_var: ContextVar[CommandContext] = ContextVar("y5n_command_context")


@dataclass
class Call:
    """A protocol-level invocation request."""

    port: str
    method: str
    args: dict | None = None
    caller_path: str | None = None


@dataclass
class Response:
    """A protocol-level invocation result."""

    result: Any = None
    error: str | None = None


def invoke(call: Call) -> Response:
    """Execute a Call through the Runtime Bus.

    The bus routes to CallHandler, which resolves the provider
    and delivers the call via the executor's transport.
    """
    from y5n.base.runtime.bus import get_bus

    return get_bus().dispatch(call)


def _set_context(ctx: CommandContext) -> None:
    _context_var.set(ctx)


class _Context:
    @staticmethod
    def current() -> CommandContext:
        try:
            return _context_var.get()
        except LookupError:
            return CommandContext()

    def request(self) -> Any:
        """Return a Request object built from the current context.

        The Request class lives in y5n.base.nodes.request and provides
        arg(), option(), has_option() etc.
        """
        from y5n.base.nodes.request import Request

        ctx = self.current()
        return Request.from_tokens(
            [ctx.command] + (ctx.tokens or []) if ctx.command else ctx.tokens
        )


context = _Context()
