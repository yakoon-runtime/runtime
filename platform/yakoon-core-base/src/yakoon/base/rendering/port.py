from typing import Any, Protocol

from yakoon.base.ui import ViewSpec

from .context import RenderContext


class RenderService(Protocol):
    async def render_view(self, ctx: RenderContext, state: str, **data) -> ViewSpec: ...


class RenderEngine(Protocol):

    async def render_str(self, template_str: str, *, context: dict) -> str: ...
    async def render_any(self, obj: Any, *, context: dict) -> Any: ...
