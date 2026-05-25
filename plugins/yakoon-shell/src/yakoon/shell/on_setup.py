from __future__ import annotations

from yakoon.base.nodes import RuntimeContext
from yakoon.base.plugins.ports import OnCompile, OnJinjaRender, OnResourceLoad
from yakoon.base.projection import Projection
from yakoon.base.resources import ResourceRef

from .ports import OnProject

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_setup(ctx: RuntimeContext):

    # --------------------------
    # --- ON PROJECT HANDLER ---
    # --------------------------

    async def _on_project(
        *,
        name: str,
        lang: str,
        state: dict | None = None,
    ) -> Projection:

        resource = ResourceRef(
            package="yakoon.shell",
            path=f"resources/{lang}/templates/{name}",
        )
        on_resource_loader = ctx.ports.get(OnResourceLoad)
        on_jinja = ctx.ports.get(OnJinjaRender)
        on_compile = ctx.ports.get(OnCompile)

        content = on_resource_loader(resource=resource)
        template = on_jinja(content=content, context={"state": state})
        return on_compile(text=template, context={})

    # ------------------------
    # --- PROVIDE INTERNAL ---
    # ------------------------

    ctx.ports.provide(OnProject, _on_project)


# ------------------------
# --- RESOURCE HANDLER ---
# ------------------------


async def _on_resource(*, domain: str, scope: str, key: str, lang: str) -> ResourceRef:

    if domain == "manual":
        return ResourceRef(
            package="yakoon.shell",
            path=f"resources/{lang}/manuals/{scope}/man",
        )

    return ResourceRef(
        package="yakoon.shell",
        path=f"resources/{lang}/templates/{scope}/{key}",
    )
