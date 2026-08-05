"""Invocation context builder (ADR-12 Section 4).

The engine owns the invocation ABI: it derives the raw context dict that
describes a call and establishes it when a flow steps. The SDK models it
into its typed ``Context``; the host reads it like any application.

The derivation happens once, at dispatch; the step only re-establishes the
already-derived dict (the flow carries it). The flow is the source of
truth; the context is its projection.
"""

from __future__ import annotations

from typing import Any

from y5n.runtime.api.runtime.context import set_context


def derive_invocation_context(
    *,
    node,
    session,
    flow_id: str,
    tokens: list[str] | None = None,
) -> dict[str, Any]:
    """Derive the invocation context dict for a node.

    ``tokens`` are the invocation arguments (as produced by the parser —
    positional args and options); when absent, they default to no
    arguments.
    """
    path = str(node.path) if node.path is not None else ""
    name = node.key or path.rsplit("/", 1)[-1]
    identity = session.get_identity() if session else None
    fs_root = session.get_data("fs:root") if session else None

    return {
        "node": {
            "path": path,
            "name": name,
        },
        "cwd": session.cwd if session else "",
        "workspace": str(fs_root) if fs_root else "",
        "user": {
            "id": str(identity) if identity else None,
            "name": session.user_name if session else None,
        },
        "session": {
            "key": str(session.key) if session else None,
            "lang": session.lang if session else None,
            "interaction": session.interaction.value if session else None,
            "data": dict(session.data.data) if session else {},
        },
        "flow": {
            "id": flow_id or "",
            "key": name,
        },
        "args": list(tokens or []),
    }


def establish_invocation_context(ctx: dict[str, Any]) -> None:
    """Make a derived invocation context current for this step."""
    set_context(ctx)
