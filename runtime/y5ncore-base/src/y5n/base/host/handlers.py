"""
Default marker handlers — the universal mapping from MarkerKind to DSL Outcome.

Every host (runtime, thread, process, …) uses these same handlers.
Only the ``drive()`` loop differs by host type.
"""

from __future__ import annotations

import json

from y5n.base.document import to_text
from y5n.base.flow.dsl import delay, delay_until, out
from y5n.base.flow.dsl import view as dsl_view

from .protocol import MarkerKind


def resolve_view(view: dict | str) -> dict:
    """Normalize a view to a dict: parse JSON strings, wrap text."""
    if isinstance(view, dict):
        return view
    if view.startswith("{"):
        try:
            data = json.loads(view)
            if isinstance(data, dict) and data.get("kind") == "document":
                return data
        except Exception:
            pass
    return to_text(view)


HANDLERS = {
    MarkerKind.WRITE: lambda m, first: out(
        resolve_view(m.value[0] if isinstance(m.value, tuple) else m.value),
        mode=(
            m.value[1]
            if isinstance(m.value, tuple) and m.value[1]
            else "replace" if first else "append"
        ),
    ),
    MarkerKind.ERROR: lambda m, _: out({"kind": "error", "text": m.value}),
    MarkerKind.DELAY: lambda m, _: delay(m.value),
    MarkerKind.DELAY_UNTIL: lambda m, _: delay_until(m.value),
    MarkerKind.VIEW: lambda m, _: dsl_view(**m.value),
}
