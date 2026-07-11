from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from y5n.base.nodes.space import NodeSpace
from y5n.base.projection import Projection
from y5n.base.resources import ResourceRef


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
    ) -> None:
        self.on_render = on_render
        self.on_render_str = on_render_str
        self.on_compile = on_compile

    async def project(
        self,
        *,
        resource: ResourceRef,
        state: dict[str, Any] | None = None,
    ) -> Projection:

        if state is None:
            state = {}

        text = self.on_render(resource=resource, context=state)

        projection = self.on_compile(text=text, context={})
        if projection.id is None:
            raise RuntimeError(
                "Renderer returned a Projection without id (parser invariant violated)"
            )

        return projection

    async def project_from_space(
        self,
        *,
        space: NodeSpace,
        resource: str = "projection",
        state: dict[str, Any] | None = None,
        resources: dict[str, dict[str, Path]] | None = None,
    ) -> Projection:
        if self.on_render_str is None:
            raise RuntimeError("OnProject port not configured")
        source = resources if resources is not None else space.resources
        variants = source.get(resource, {}) if source else {}
        template_path = self._resolve_variant(variants, space.session.lang)
        if template_path is None:
            raise FileNotFoundError(
                f"Template not found: resource={resource}, lang={space.session.lang}"
            )
        template = template_path.read_text()
        html = self.on_render_str(template, state or {})
        return self.on_compile(text=html, context={})

    # ----------------------------------
    # INTERNALS
    # ----------------------------------

    def _resolve_variant(self, variants: dict[str, Any], lang: str) -> Any | None:
        return variants.get(lang) or variants.get("default")


# ----------------------------------
# PORTS
# ----------------------------------


class OnRender(Protocol):
    def __call__(self, *, resource: ResourceRef, context: dict[str, Any]) -> str: ...


class OnCompile(Protocol):
    def __call__(self, *, text: str, context: dict) -> Projection: ...
