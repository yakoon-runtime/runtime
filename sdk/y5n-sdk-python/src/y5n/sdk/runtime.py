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


def resolve(
    node_path: str,
    capability: str,
    parameters: dict[str, Any] | None = None,
):
    """Resolve a node's content capability into a ``Resource`` (awaitable).

    ``node_path`` identifies the declaring node; the runtime dispatches to
    the node's host (ADR-10).
    """
    from .ports import get

    return get("runtime.resource").resolve(
        node_path=node_path,
        capability=capability,
        parameters=parameters or {},
    )


def supports(node_path: str, capability: str):
    """Ask whether a node's host can resolve a capability (awaitable)."""
    from .ports import get

    return get("runtime.resource").supports(
        node_path=node_path,
        capability=capability,
    )


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
