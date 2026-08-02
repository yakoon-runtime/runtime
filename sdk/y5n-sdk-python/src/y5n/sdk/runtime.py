"""Runtime — backward-compatible facade for all domain modules.

Prefer importing domain modules directly:

    from y5n.sdk import fs, io, timer, scheduler, network, viewport

Resource resolution (ADR-10):

    from y5n.sdk import runtime

    resource = await runtime.resolve("resource:y5n.docs.info:man")
    text = resource.read_text()
"""

from __future__ import annotations

from typing import Any

from .fs import fs
from .io import io
from .network import network
from .scheduler import scheduler
from .session import session
from .timer import timer
from .viewport import viewport


def resolve(ref: str, parameters: dict[str, Any] | None = None):
    """Resolve a resource reference into a ``Resource`` (awaitable)."""
    from .ports import get

    return get("runtime.resource").resolve(ref=ref, parameters=parameters or {})


def supports(ref: str):
    """Ask the runtime whether a reference can be resolved (awaitable)."""
    from .ports import get

    return get("runtime.resource").supports(ref=ref)


__all__ = [
    "fs",
    "io",
    "network",
    "resolve",
    "scheduler",
    "session",
    "supports",
    "timer",
    "viewport",
]
