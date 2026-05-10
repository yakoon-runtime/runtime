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
from yakoon.base.sources import (
    DataRequest,
    OnDataSource,
)


class CmdLs(Command):

    key = "ls"

    anonymous = True
    scope = CommandScope.GLOBAL
    invocations = [Invocation(default=True)]

    def __init__(
        self,
        on_project: OnProjectCmd,
        on_source: OnDataSource,
        on_get_active_app: OnGetActiveApp,
        on_get_session: OnGetSession,
    ):
        self.on_project = on_project
        self.on_source = on_source
        self.on_get_active_app = on_get_active_app
        self.on_get_session = on_get_session

    async def run(
        self,
        request: Request,
    ):
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
            return

        discovery = result.one()

        projection = await self.on_project(
            name="overview.sam",
            state={
                "mode": discovery["mode"],
                "commands": discovery["commands"],
                "apps": discovery["apps"],
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


class OnGetActiveApp(Protocol):

    def __call__(self) -> str | None: ...


class OnGetSession(Protocol):
    def __call__(self) -> object: ...
