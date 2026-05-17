from __future__ import annotations

from typing import Any, Protocol

from yakoon.base.projection import Projection
from yakoon.base.resources import ResourceRef

from .compiler import ResolverContext


class Projector:
    """
    Unified projector.

    Responsibilities:
      - render a view into a UI document
    """

    def __init__(
        self,
        on_render: OnRender,
        on_compile: OnCompile,
    ) -> None:
        self.on_render = on_render
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
        context = ResolverContext(assets=resource)  # TODO:

        projection = self.on_compile(text=text, ctx=context)
        if projection.id is None:
            raise RuntimeError(
                "Renderer returned a Projection without id (parser invariant violated)"
            )

        return projection


# ----------------------------------
# PORTS
# ----------------------------------


class OnRender(Protocol):
    def __call__(self, *, resource: ResourceRef, context: dict[str, Any]) -> str: ...


class OnCompile(Protocol):
    def __call__(self, *, text: str, ctx: ResolverContext) -> Projection: ...
