from __future__ import annotations

from typing import Any

from yakoon.base.projection.model import Projection

# from yakoon.base.projection.port import ProjectionParser # TODO: ProjectionMapper & DI
from yakoon.base.projection.rendering import RenderContext, RenderEngine
from yakoon.base.resources import ResourceLoader
from yakoon.base.runtime import Container

from ..parser import ProjectionMapper, build_ast, tokenize_text


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

        # 1) Jinja render
        rendered_text = await engine.render_str(source, context=context)

        # 2) tokenize
        tokens = tokenize_text(rendered_text)

        # 3) build AST
        ast = build_ast(tokens)

        # 4) create mapping
        mapper = ProjectionMapper()
        projection = mapper.map_projection(ast)
        return projection
