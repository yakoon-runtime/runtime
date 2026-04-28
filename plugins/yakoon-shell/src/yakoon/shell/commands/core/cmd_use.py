from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from yakoon.base.application.application import Application
from yakoon.base.commands import Command, Request
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.flow import out
from yakoon.base.projection import to_text


class CmdUse(Command):

    key = "use"

    def __init__(
        self,
        on_project: OnProjectCmd,
        on_get_app: OnGetApp,
        on_list_apps: OnGetApps,
        on_get_active_app: OnGetActiveApp,
        on_set_active_app: OnSetActiveApp,
        on_save_session: OnSaveSession,
    ):
        self.on_project = on_project
        self.on_get_app = on_get_app
        self.on_list_apps = on_list_apps
        self.on_get_active_app = on_get_active_app
        self.on_set_active_app = on_set_active_app
        self.on_save_session = on_save_session

    async def run(self, request: Request):

        applications = []

        name = request.arg(0)
        if not name:
            applications = self.on_list_apps()
        else:
            app = self.on_get_app(app_id=name)
            if app:
                applications.append(app)

        if applications and not name:
            projection = await self.on_project(
                name="active.sam",
                state={
                    "apps": applications,
                },
            )
            yield out(projection)

        elif applications:
            if name == self.on_get_active_app():
                projection = await self.on_project(
                    name="using.sam",
                    state={
                        "app": applications[0],
                    },
                )
                yield out(projection)
            else:
                self.on_set_active_app(app_id=name)
                await self.on_save_session()
                yield out(to_text(f"Aktiver Kontext: {name}"))

        else:
            projector = await self.on_project(
                name="error.sam",
                state={
                    "app": name,
                },
            )
            yield out(projector)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetApps(Protocol):
    def __call__(self) -> Sequence[Application]: ...


class OnGetApp(Protocol):
    def __call__(self, *, app_id: str) -> Application | None: ...


class OnSaveSession(Protocol):
    async def __call__(self) -> None: ...


class OnGetActiveApp(Protocol):
    def __call__(self) -> str | None: ...


class OnSetActiveApp(Protocol):
    def __call__(self, *, app_id: str) -> None: ...
