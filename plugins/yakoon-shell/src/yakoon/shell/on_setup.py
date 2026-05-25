from __future__ import annotations

from yakoon.base.nodes import NodePath, NodeSpace
from yakoon.base.plugins.ports import (
    OnErrorResolve,
    OnManualResolve,
    OnProjectionResolve,
)
from yakoon.base.projection import Projection
from yakoon.base.resources import ResourceRef

from .ports import OnProject

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_setup(space: NodeSpace):

    # ------------------
    # --- ON PROJECT ---
    # ------------------

    async def on_project(
        *,
        name: str,
        lang: str,
        state: dict | None = None,
    ) -> Projection:

        resource = ResourceRef(
            package="yakoon.shell",
            path=f"resources/{lang}/templates/{name}",
        )

        on_project = space.ports.get(OnProjectionResolve)
        return await on_project(resource=resource, state=state)

    # ------------------
    # --- ON MANUAL ---
    # ------------------

    async def on_manual(
        *,
        key: NodePath,
        lang: str,
        state: dict | None = None,
    ) -> Projection:

        resource = ResourceRef(
            package="yakoon.shell",
            path=f"resources/{lang}/manuals/{key.parent.last}/{key.last}",
        )

        on_project = space.ports.get(OnProjectionResolve)
        return await on_project(resource=resource, state=state)

    # ------------------
    # --- ON MANUAL ---
    # ------------------

    async def on_error(
        *,
        exc: Exception,
        lang: str,
    ) -> Projection:

        resource = ResourceRef(
            package="yakoon.shell",
            path=f"resources/{lang}/errors/exc",
        )

        on_project = space.ports.get(OnProjectionResolve)

        return await on_project(
            resource=resource,
            state={
                "key": exc.args[0].key,
            },
        )

    # ------------------------
    # --- PROVIDE INTERNAL ---
    # ------------------------

    space.ports.provide(OnProject, on_project)
    space.ports.provide(OnManualResolve, on_manual)
    space.ports.provide(OnErrorResolve, on_error)
