from __future__ import annotations

import yaml

from yakoon.base.rendering import RenderContext, RenderEngine
from yakoon.base.resources import ResourceLoader
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.ui import View, ViewSpecParser


class DefaultRenderService:

    def __init__(self, services: ServiceDirectory) -> None:
        self._services = services

    async def render_view(self, ctx: RenderContext, state: str, **data) -> View:
        loader = self._services.get(ResourceLoader)
        source = loader.load_text(ctx.resource.child(state))

        # 1) render full template text (Jinja)
        engine = self._services.get(RenderEngine)

        # reserved namespaces owned by the platform
        meta = {"state": state, "resource": ctx.resource.path}

        reserved = {"_meta"}  # later: _host, _ui, _env, _i18n ...?
        collisions = reserved.intersection(data.keys())
        if collisions:
            raise KeyError(
                f"Template context keys reserved by platform: {sorted(collisions)}. "
                "Please rename your payload fields."
            )

        context = dict(data)
        context["_meta"] = meta

        rendered_text = await engine.render_str(source, context=context)

        # 2) validate YAML root early (nice error messages)
        raw = yaml.safe_load(rendered_text)
        if not isinstance(raw, dict):
            raise TypeError("Root template must be a mapping")

        # 3) parse/validate into View
        View = self._services.get(ViewSpecParser)
        return View.parse_spec(rendered_text)
