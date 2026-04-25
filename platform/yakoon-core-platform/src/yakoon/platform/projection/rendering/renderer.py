from __future__ import annotations

from typing import Any

from typing_extensions import Protocol

from yakoon.base.resources import ResourceRef


class TemplateProjectionRenderer:

    def __init__(
        self,
        on_load_resource: OnLoadResource,
        on_engine_render: OnEngineRender,
    ):
        self.on_load_resouce = on_load_resource
        self.on_engine_render = on_engine_render

    def render(self, resource: ResourceRef, context: dict[str, Any]) -> str:

        template_str = self.on_load_resouce(resource=resource)

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
            template_str=template_str,
            context=data,
        )
        return template_string


# ----------------------------------
# PORTS
# ----------------------------------


class OnLoadResource(Protocol):
    def __call__(self, *, resource: ResourceRef) -> str: ...


class OnEngineRender(Protocol):
    def __call__(self, *, template_str: str, context: dict) -> str: ...
