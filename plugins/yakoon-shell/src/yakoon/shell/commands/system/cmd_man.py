from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import (
    Command,
    CommandScope,
    Invocation,
    Request,
)
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.flow import out
from yakoon.base.projection import Projection
from yakoon.base.sources import (
    DataRequest,
    OnDataSource,
)


class CmdMan(Command):

    key = "man"

    anonymous = True
    scope = CommandScope.GLOBAL
    invocations = [Invocation(args=["command"], default=True)]

    def __init__(
        self,
        on_source: OnDataSource,
        on_project: OnProjectCmd,
        on_project_manual: OnProjectManual,
        on_get_active_app: OnGetActiveApp,
        on_get_session: OnGetSession,
    ):
        self.on_source = on_source
        self.on_project = on_project
        self.on_project_manual = on_project_manual
        self.on_get_active_app = on_get_active_app
        self.on_get_session = on_get_session

    async def run(
        self,
        request: Request,
    ):

        command_key = request.arg(0)

        # --------------------------------------------------
        # Runtime discovery
        # --------------------------------------------------

        result = await self.on_source(
            DataRequest(
                "system:discovery --runtime",
                context={
                    "session": self.on_get_session(),
                    "mode": self.resolve_mode(request),
                    "app_id": self.on_get_active_app(),
                },
            )
        )

        if result.status != "ok":
            projection = await self.on_project(
                name="error.sam",
                state={
                    "command_key": command_key,
                },
            )

            yield out(projection)
            return

        discovery = result.one()

        # --------------------------------------------------
        # Resolve command
        # --------------------------------------------------

        command = next(
            (c for c in discovery["commands"] if c["key"] == command_key),
            None,
        )

        if not command:
            projection = await self.on_project(
                name="error.sam",
                state={
                    "command_key": command_key,
                },
            )

            yield out(projection)
            return

        # --------------------------------------------------
        # Resolve app
        # --------------------------------------------------

        result = await self.on_source(
            DataRequest(f"system:apps --by-id {command['app_id']}")
        )

        if result.status != "ok":
            projection = await self.on_project(
                name="error.sam",
                state={
                    "command_key": command_key,
                },
            )

            yield out(projection)
            return

        app = result.one()

        # --------------------------------------------------
        # Render manual
        # --------------------------------------------------

        controller_id = command["controller_id"]

        try:

            resources = app["resources"][controller_id]

            projection = await self.on_project_manual(
                resources=resources,
                name="manual.sam",
                state={
                    "command_key": command_key,
                },
            )

            yield out(projection)

        except LookupError:

            projection = await self.on_project(
                name="error.sam",
                state={
                    "command_key": command_key,
                },
            )

            yield out(projection)

    def resolve_mode(
        self,
        request: Request,
    ) -> str:

        if request.has_option("internal"):
            return "internal"

        if request.has_option("all"):
            return "all"

        return "default"


# --------------------------------------------------
# PORTS
# --------------------------------------------------


class OnProjectManual(Protocol):

    async def __call__(
        self,
        *,
        resources: dict,
        name: str,
        state: dict,
    ) -> Projection: ...


class OnGetSession(Protocol):
    def __call__(self) -> object: ...


class OnGetActiveApp(Protocol):

    def __call__(
        self,
    ) -> str | None: ...
