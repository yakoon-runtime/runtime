from __future__ import annotations

from typing import Protocol

from yakoon.base.controllers.resolver import resolve_resource
from yakoon.base.errors.state import ErrorState
from yakoon.base.plugins.ports import OnProject
from yakoon.base.projection import Projection
from yakoon.base.resources.resource import ResourceRef
from yakoon.platform.runtime import Session


class ErrorProjector:

    PACKAGE = package = "yakoon.platform"
    CONTRACTS = "errors/{lang}/{cmd_key}"

    def __init__(
        self,
        on_project: OnProject,
        on_extract: OnExtractError,
    ):
        self.on_project = on_project
        self.on_extract = on_extract

    async def project(self, exc: Exception, session: Session) -> Projection:

        state = self.on_extract(exc)

        path = resolve_resource(
            i18n_root=self.CONTRACTS,
            lang=session.lang,
            cmd_key=state.code,
        )

        state.data = state.data or {}
        state.data["debug"] = session.debug

        resource = ResourceRef(self.PACKAGE, path)
        return await self.on_project(
            resource=resource,
            state=state.data,
        )


# ----------------------------------
# PORTS
# ----------------------------------


class OnExtractError(Protocol):
    def __call__(self, error: Exception) -> ErrorState: ...
