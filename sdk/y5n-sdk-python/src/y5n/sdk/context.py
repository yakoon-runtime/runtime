"""Execution context — answers "where am I?".

This module is read-only. It provides the frozen snapshot of
the current invocation's starting conditions.

Usage:
    from y5n.sdk import context

    ctx = context.current()
    req = context.request()
    ses = context.session()
"""

from __future__ import annotations

from contextvars import ContextVar

from .libs.models import Context as _Ctx
from .libs.models import Flow as _Flow
from .libs.models import Request as _Request
from .libs.models import Session as _Session

_var: ContextVar[_Ctx] = ContextVar("y5n_sdk_context")


def _set(ctx: _Ctx) -> None:
    """Set the current context (called by the Host)."""
    _var.set(ctx)


def current() -> _Ctx:
    """Return the current execution context."""
    try:
        return _var.get()
    except LookupError:
        return _Ctx()


def request() -> _Request:
    """Return a Request object parsed from the current context tokens."""
    ctx = current()
    return _Request.from_tokens(ctx.tokens)


def session() -> _Session:
    """Return a Session object built from the current context."""
    ctx = current()
    return _Session.from_context(ctx.session, ctx.user)


def flow() -> _Flow:
    """Return a Flow object built from the current context."""
    ctx = current()
    return _Flow.from_dict(ctx.flow)


__all__ = ["current", "flow", "request", "session"]
