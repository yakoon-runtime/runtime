"""Execution context — answers "where am I?".

This module is read-only. It provides the frozen snapshot of
the current invocation's starting conditions.

The raw invocation context is set by the engine through the Runtime API
(ADR-12 Section 4); this module is the typed, ergonomic view on it.

Usage:
    from y5n.sdk import context

    ctx = context.current()
    req = context.request()
    ses = context.session()
"""

from __future__ import annotations

from y5n.runtime.api.runtime.context import current_context

from .libs.models import Context as _Ctx
from .libs.models import Flow as _Flow
from .libs.models import Request as _Request
from .libs.models import Session as _Session


def current() -> _Ctx:
    """Return the current execution context."""
    return _Ctx.from_dict(current_context())


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
