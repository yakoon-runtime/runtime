from __future__ import annotations

from typing import Any

from yakoon.base.projection import Projection
from yakoon.base.projection.compiler import ProjectionCompiler
from yakoon.base.projection.rendering import ProjectionRenderer, RenderContext
from yakoon.base.resources import ResourceRef
from yakoon.base.runtime import Container
from yakoon.platform.runtime.sessions import Session


class TemplateProjector:
    """
    Unified projector.

    Responsibilities:
      - render a view into a UI document
    """

    def __init__(
        self,
        resource: ResourceRef,
        session: Session,
        container: Container,
    ) -> None:
        self._session = session
        self._renderer = container.get(ProjectionRenderer)
        self._compiler = container.get(ProjectionCompiler)

        self._ctx = RenderContext(
            resource=resource,
            lang=session.lang,
        )

    async def project(
        self,
        name: str,
        state: dict[str, Any] | None = None,
    ) -> Projection:

        if state is None:
            state = {}

        text = await self._renderer.render(self._ctx, name, state)
        projection = self._compiler.compile(text)
        if projection.id is None:
            raise RuntimeError(
                "Renderer returned a Projection without id (parser invariant violated)"
            )

        return projection
