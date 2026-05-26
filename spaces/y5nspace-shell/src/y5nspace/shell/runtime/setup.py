from __future__ import annotations

from y5n.api.nodes import NodePath, NodeSpace
from y5n.api.ports import (
    OnErrorResolve,
    OnManualResolve,
    OnProjectionResolve,
)
from y5n.api.projections import Projection
from y5n.api.resources import ResourceRef
from y5n.api.sessions import Session

from ..ports import OnProject

# ----------------------------------
# COMMAND
# ----------------------------------


async def setup(space: NodeSpace):

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
            package="y5nspace.shell",
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
            package="y5nspace.shell",
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
            package="y5nspace.shell",
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
