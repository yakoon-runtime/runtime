from __future__ import annotations

from typing import Any

import yaml

from yakoon.base import ports
from yakoon.base.directories.service import ServiceDirectory
from yakoon.base.models.view import ViewSpec
from yakoon.platform.runtime.render.context import RenderContext
from yakoon.platform.runtime.render.section import RenderSection


class RendererService:

    def __init__(
        self,
        services: ServiceDirectory,
    ):
        self._services = services

    async def render_view(
        self, ctx: RenderContext, section_key: str, **data
    ) -> ViewSpec:
        loader = self._services.get(ports.FileLoader)
        source = loader.load_text(ctx.resource)

        raw = yaml.safe_load(source)
        if not isinstance(raw, dict):
            raise TypeError("Root template must be a mapping")

        kind = raw.get("kind")
        if kind != "command_view":
            raise TypeError(f"Unknown root kind: {kind!r}")

        mode = raw.get("mode", "replace")
        views = raw.get("views") or {}
        inputs = raw.get("inputs") or {}
        if not isinstance(views, dict) or not isinstance(inputs, dict):
            raise TypeError(
                "command_view.views and command_view.inputs must be mappings"
            )

        # select
        if section_key in views:
            selected_ns = "views"
            selected = views[section_key]
        elif section_key in inputs:
            selected_ns = "inputs"
            selected = inputs[section_key]
        else:
            raise ValueError(
                f"Unknown section_key {section_key!r}. \
                    Expected one of views={sorted(views.keys())} or inputs={sorted(inputs.keys())}."
            )

        # render only selected (recursively for all strings)
        section = RenderSection(section_key, data)
        engine = self._services.get(ports.RenderEngine)
        rendered_selected = await engine.render_any(selected, section=section)

        minimal: dict[str, Any] = {
            "kind": "command_view",
            "mode": mode,
            "views": {},
            "inputs": {},
        }
        minimal[selected_ns][section_key] = rendered_selected

        yaml_text = yaml.safe_dump(minimal, sort_keys=False, allow_unicode=True)
        viewspec = self._services.get(ports.ViewSpecService)
        return viewspec.parse_spec(yaml_text, section_key=section_key)
