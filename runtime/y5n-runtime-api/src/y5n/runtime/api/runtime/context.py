"""Invocation ABI — which data describes the current call.

This is one of the three ABIs of the Runtime API:

* ``context.py`` — the invocation ABI: which data describes the current call.
* ``invoke.py`` — the port ABI: which capability is being called.
* ``flow/`` — the flow ABI: how an execution advances (Pulse, AwaitEvent, ...).

The invocation ABI answers "who am I, where do I run, with which tokens?".
The engine sets it once, before the flow starts (ADR-12 Section 4). The data
is a plain dict — the runtime only transports it; the SDK models it into its
typed ``Context`` (ADR-11).
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_context_var: ContextVar[dict[str, Any]] = ContextVar("y5n_invocation_context")


def set_context(data: dict[str, Any]) -> None:
    """Set the invocation context for the current execution (engine-side).

    Called exactly once, before the flow starts. The data is a plain dict —
    the SDK reads the same variable and models it into its typed Context.
    """
    _context_var.set(data)


def current_context() -> dict[str, Any]:
    """Return the current raw invocation context, or an empty snapshot."""
    try:
        return _context_var.get()
    except LookupError:
        return {}
