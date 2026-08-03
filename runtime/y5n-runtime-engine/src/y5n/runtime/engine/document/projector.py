from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from y5n.runtime.api.nodes.space import NodeSpace
from y5n.runtime.api.resources import ResourceRef
from y5n.runtime.engine.resources.host import resolve_via_host


class Projector:
    """
    Unified projector.

    Responsibilities:
      - render a view into a UI document
      - resolve projections from node resources
    """

    def __init__(
        self,
        on_render: OnRender,
        on_render_str: Callable[[str, dict], str],
        on_compile: OnCompile,
        tree=None,
    ) -> None:
        self.on_render = on_render
        self.on_render_str = on_render_str
        self.on_compile = on_compile
        self._tree = tree

    async def project(
        self,
        *,
        resource: ResourceRef,
        state: dict[str, Any] | None = None,
    ) -> dict:

        if state is None:
            state = {}

        text = self.on_render(resource=resource, context=state)

        document = self.on_compile(text=text, context={})
        if document.get("id") is None:
            raise RuntimeError(
                "Renderer returned a Document without id (parser invariant violated)"
            )

        return document

    async def project_from_space(
        self,
        *,
        space: NodeSpace,
        resource: str = "document",
        state: dict[str, Any] | None = None,
    ) -> dict:
        if self.on_render_str is None:
            raise RuntimeError("OnProject port not configured")
        if self._tree is None:
            raise RuntimeError("Projector has no tree configured")
        node = self._tree.find(str(space.path))
        if node is None:
            raise FileNotFoundError(f"Node not found: {space.path}")
        params: dict[str, Any] = {"name": "default", "lang": space.session.lang}
        content = await resolve_via_host(self._tree, node, resource, params)
        template = content.read_text()
        html = self.on_render_str(template, state or {})
        return self.on_compile(text=html, context={})


# ----------------------------------
# PORTS
# ----------------------------------


class OnRender(Protocol):
    def __call__(self, *, resource: ResourceRef, context: dict[str, Any]) -> str: ...


class OnCompile(Protocol):
    def __call__(self, *, text: str, context: dict) -> dict: ...
