from __future__ import annotations

from typing import Any

from typing_extensions import Protocol
from y5n.runtime.engine.resources import ResourceRef


class Renderer:

    def __init__(
        self,
        on_load_resource: OnLoadResource,
        on_engine_render: OnEngineRender,
    ):
        self.on_load_resouce = on_load_resource
        self.on_engine_render = on_engine_render

    def render(self, resource: ResourceRef, context: dict[str, Any]) -> str:

        content = self.on_load_resouce(resource=resource)

        # reserved namespaces owned by the platform
        meta = {"resource": resource}

        reserved = {"_meta"}  # later: _host, _ui, _env, _i18n ...?
        collisions = reserved.intersection(context.keys())
        if collisions:
            raise KeyError(
                f"Template context keys reserved by platform: {sorted(collisions)}. "
                "Please rename your payload fields."
            )

        data = {
            "state": context,
            "_meta": meta,
        }

        template_string = self.on_engine_render(
            content=content,
            context=data,
        )
        return template_string

    def render_str(self, content: str, context: dict) -> str:
        return self.on_engine_render(content=content, context=context)


# ----------------------------------
# PORTS
# ----------------------------------


class OnLoadResource(Protocol):
    def __call__(self, *, resource: ResourceRef) -> str: ...


class OnEngineRender(Protocol):
    def __call__(self, *, content: str, context: dict) -> str: ...
