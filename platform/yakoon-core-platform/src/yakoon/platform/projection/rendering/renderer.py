from __future__ import annotations

from typing import Any

from yakoon.base.projection.rendering import RenderContext, RenderEngine
from yakoon.base.resources import ResourceLoader
from yakoon.base.runtime import Container


class TemplateProjectionRenderer:

    def __init__(self, container: Container) -> None:
        self._container = container

    async def render(self, ctx: RenderContext, name: str, state: dict[str, Any]) -> str:
        loader = self._container.get(ResourceLoader)
        source = loader.load_text(ctx.resource.child(name))

        # 1) render full template text (Jinja)
        engine = self._container.get(RenderEngine)

        # reserved namespaces owned by the platform
        meta = {"name": name, "resource": ctx.resource.path}

        reserved = {"_meta"}  # later: _host, _ui, _env, _i18n ...?
        collisions = reserved.intersection(state.keys())
        if collisions:
            raise KeyError(
                f"Template context keys reserved by platform: {sorted(collisions)}. "
                "Please rename your payload fields."
            )

        context = {
            "state": state,
            "_meta": meta,
        }

        template_string = await engine.render_str(source, context=context)
        return template_string
