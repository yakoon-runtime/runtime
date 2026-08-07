"""Adapter: document port for SDK.

Registered as ``"document"`` on the Runtime Bus.
Receives the full ``Call`` as first argument,
so the caller_path is available without polluting the
business args.
"""

from __future__ import annotations

import json
from typing import Any

from y5n.runtime.api.document.normalize import normalize
from y5n.runtime.api.runtime.invoke import Call
from y5n.runtime.engine.resources.host import resolve_via_host


class DocumentAdapter:
    """SDK-facing document Port."""

    def __init__(self, projector, tree):
        self._projector = projector
        self._tree = tree

    async def render(
        self,
        call: Call,
        *,
        name: str = "default",
        state: dict[str, Any] | None = None,
        lang: str = "en",
    ) -> str:
        node = self._tree.find(call.caller_path)
        if not node:
            assert call.caller_path
            return _error_json(call.caller_path)

        params: dict[str, Any] = {"name": name, "lang": lang}
        if state:
            # The variant selector (name/variant/lang) must survive the
            # state merge: state feeds the template, the selector picks
            # the resource. If a template state field collides with the
            # selector key (e.g. state={"name": ...}), the selector wins.
            params = {**state, **params}

        try:
            resource = await resolve_via_host(self._tree, node, "document", params)
        except LookupError:
            assert call.caller_path
            return _error_json(call.caller_path, name)

        template = resource.read_text()
        rendered = self._projector.on_render_str(template, context=state or {})
        doc = normalize(self._projector.on_compile(text=rendered, context={}))
        return json.dumps(doc, default=str)


def _error_json(path: str, name: str = "") -> str:
    msg = (
        f"error: document '{name}' not found at '{path}'"
        if name
        else f"error: node not found at '{path}'"
    )
    doc = {
        "kind": "document",
        "header": {"role": "info"},
        "blocks": [{"type": "text", "text": [{"type": "text", "text": msg}]}],
    }
    return json.dumps(doc, default=str)
