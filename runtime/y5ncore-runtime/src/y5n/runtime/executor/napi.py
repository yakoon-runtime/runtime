"""
y5napi — yakoon API for the Python executor.

Provides access to the runtime context for scripts running
under the python executor (executor: python).

Usage:

    from y5n.api.napi import context

    req = context.current().request
    print(req.arg(0) if req else "no args")
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from y5n.base.nodes.node import NodePath
    from y5n.base.nodes.ports import NodePorts
    from y5n.base.nodes.request import Request
    from y5n.runtime.runtime import Session


@dataclass
class CommandContext:
    request: Request | None = None
    session: Session | None = None
    ports: NodePorts | None = None
    path: NodePath | None = None


_context_var: ContextVar[CommandContext] = ContextVar("y5n_context")


def _set_context(ctx: CommandContext) -> None:
    _context_var.set(ctx)


class _Context:
    """Entry point for accessing the runtime context.

    Usage:
        ctx = context.current()
        req = ctx.request
        ses = ctx.session
        path = ctx.path
    """

    @staticmethod
    def current() -> CommandContext:
        try:
            return _context_var.get()
        except LookupError:
            return CommandContext()


context = _Context()
