from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import Command, Request
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.flow import out
from yakoon.base.projection import to_text
from yakoon.base.sources import DataRequest, OnDataSource


class CmdUse(Command):

    key = "use"

    def __init__(
        self,
        on_source: OnDataSource,
        on_project: OnProjectCmd,
        on_get_active_app: OnGetActiveApp,
        on_set_active_app: OnSetActiveApp,
        on_save_session: OnSaveSession,
    ):
        self.on_source = on_source
        self.on_project = on_project
        self.on_get_active_app = on_get_active_app
        self.on_set_active_app = on_set_active_app
        self.on_save_session = on_save_session

    async def run(self, request: Request):

        applications = []

        app_id = ""
        app_name = request.arg(0)
        if not app_name:
            data = await self.on_source(DataRequest("system:apps --all"))
            applications = data.rows
        else:
            data = await self.on_source(
                DataRequest(f"system:apps --by-name {app_name}")
            )
            app = data.one_or_none()
            if app:
                app_id = app["id"]
                applications.append(app)

        if applications and not app_id:
            projection = await self.on_project(
                name="active.sam",
                state={
                    "apps": applications,
                },
            )
            yield out(projection)

        elif applications:
            if app_id == self.on_get_active_app():
                projection = await self.on_project(
                    name="using.sam",
                    state={
                        "app": applications[0],
                    },
                )
                yield out(projection)
            else:
                self.on_set_active_app(app_id=app_id)
                await self.on_save_session()
                yield out(to_text(f"Aktiver Kontext: {app_name}"))

        else:
            projector = await self.on_project(
                name="error.sam",
                state={
                    "app": app_name,
                },
            )
            yield out(projector)


# ----------------------------------
# PORTS
# ----------------------------------


class OnSaveSession(Protocol):
    async def __call__(self) -> None: ...


class OnGetActiveApp(Protocol):
    def __call__(self) -> str | None: ...


class OnSetActiveApp(Protocol):
    def __call__(self, *, app_id: str) -> None: ...
