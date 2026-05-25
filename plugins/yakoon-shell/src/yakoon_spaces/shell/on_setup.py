from __future__ import annotations

from yakoon.api.nodes import NodePath, NodeSpace
from yakoon.api.ports import (
    OnErrorResolve,
    OnManualResolve,
    OnProjectionResolve,
)
from yakoon.api.projections import Projection
from yakoon.api.resources import ResourceRef
from yakoon.api.sessions import Session

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
            package="yakoon_spaces.shell",
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
            package="yakoon_spaces.shell",
            path=f"resources/{lang}/manuals/{key.parent.last}/{key.last}",
        )

        on_project = space.ports.get(OnProjectionResolve)
        return await on_project(resource=resource, state=state)

    # ------------------
    # --- ON MANUAL ---
    # ------------------

    async def on_error(
        *,
        key: NodePath,
        session: Session,
        error: Exception,
    ) -> Projection:

        resource = ResourceRef(
            package="yakoon_spaces.shell",
            path=f"resources/{session.lang}/errors/exc",
        )

        on_project = space.ports.get(OnProjectionResolve)

        return await on_project(
            resource=resource,
            state={"message": error.args[0]},
        )

    # ------------------------
    # --- PROVIDE INTERNAL ---
    # ------------------------

    space.ports.provide(OnProject, on_project)
    space.ports.provide(OnManualResolve, on_manual)
    space.ports.provide(OnErrorResolve, on_error)
