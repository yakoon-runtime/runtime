from __future__ import annotations

from typing import Any

import yaml

from yakoon.base.projection.model import Projection
from yakoon.base.projection.port import ProjectionParser
from yakoon.base.projection.rendering import RenderContext, RenderEngine
from yakoon.base.resources import ResourceLoader
from yakoon.base.runtime import Container


class TemplateProjectionRenderer:

    def __init__(self, container: Container) -> None:
        self._container = container

    async def render(
        self, ctx: RenderContext, name: str, state: dict[str, Any]
    ) -> Projection:
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

        rendered_text = await engine.render_str(source, context=context)

        # 2) validate YAML root early (nice error messages)
        raw = yaml.safe_load(rendered_text)
        if not isinstance(raw, dict):
            raise TypeError("Root template must be a mapping")

        # 3) parse/validate into View
        parser = self._container.get(ProjectionParser)
        return parser.parse_spec(rendered_text)
