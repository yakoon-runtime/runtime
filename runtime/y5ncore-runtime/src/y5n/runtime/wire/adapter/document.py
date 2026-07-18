"""Adapter: document port for SDK.

Registered as ``"document"`` on the Runtime Bus.
Receives the full ``Call`` as first argument,
so the caller_path is available without polluting the
business args.
"""

from __future__ import annotations

from typing import Any

from y5n.base.runtime.context import Call


class DocumentAdapter:
    """SDK-facing document Port."""

    def __init__(self, projector, tree):
        self._projector = projector
        self._tree = tree

    def render(
        self,
        call: Call,
        *,
        name: str = "default",
        state: dict[str, Any] | None = None,
        lang: str = "en",
    ) -> str:
        node = self._tree.find(call.caller_path)
        if not node:
            return f"error: node not found at '{call.caller_path}'"

        variants = (node.resources or {}).get("document", {})
        template_path = (
            variants.get(lang) or variants.get(name) or variants.get("default")
        )
        if not template_path:
            return f"error: projection '{name}' not found"

        template = template_path.read_text()
        rendered = self._projector.on_render_str(template, context=state or {})
        return rendered
