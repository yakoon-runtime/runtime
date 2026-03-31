from typing import Any, Protocol

from yakoon.base.projection import Projection

from .context import RenderContext


class ProjectionRenderer(Protocol):
    async def render(
        self, ctx: RenderContext, name: str, state: dict[str, Any]
    ) -> Projection: ...


class RenderEngine(Protocol):

    async def render_str(self, template_str: str, *, context: dict) -> str: ...
    async def render_any(self, obj: Any, *, context: dict) -> Any: ...
