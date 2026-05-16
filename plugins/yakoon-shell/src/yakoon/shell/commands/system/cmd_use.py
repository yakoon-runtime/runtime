from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import (
    Command,
    Invocation,
    Request,
)
from yakoon.base.flow import out
from yakoon.base.plugins.ports import OnProject
from yakoon.base.projection import to_text
from yakoon.base.sources import (
    DataRequest,
    OnDataSource,
)


class CmdUse(Command):

    key = "use"

    anonymous = True

    invocations = [
        Invocation(),
    ]

    def __init__(
        self,
        on_source: OnDataSource,
        on_project: OnProject,
        on_get_active_app: OnGetActiveApp,
        on_set_active_app: OnSetActiveApp,
        on_save_session: OnSaveSession,
    ):
        self.on_source = on_source
        self.on_project = on_project
        self.on_get_active_app = on_get_active_app
        self.on_set_active_app = on_set_active_app
        self.on_save_session = on_save_session

    async def run(
        self,
        request: Request,
    ):

        app_name = request.arg(0)

        # --------------------------------------------------
        # use
        # --------------------------------------------------

        if not app_name:
            data = await self.on_source(DataRequest("system:apps --all"))
            projection = await self.on_project(
                key="use:active",
                scope="shell",
                lang=request.lang,
                state={
                    "apps": data.rows,
                },
            )
            yield out(projection)
            return

        # --------------------------------------------------
        # use ..
        # --------------------------------------------------
        if app_name == "..":
            result = await self.on_source(DataRequest("system:apps --shell"))
            if result.status != "ok":
                return

            shell = result.one()
            current = self.on_get_active_app()

            # already shell
            if current == shell["id"]:
                yield out(to_text(f"Aktiver Kontext: {shell['id']}"))
                return

            self.on_set_active_app(app_id=shell["id"])
            await self.on_save_session()

            yield out(to_text(f"Aktiver Kontext: {shell['id']}"))
            return

        # --------------------------------------------------
        # use <app>
        # --------------------------------------------------

        data = await self.on_source(DataRequest(f"system:apps --by-name {app_name}"))
        app = data.one_or_none()
        if not app:
            projection = await self.on_project(
                key="use:error",
                scope="shell",
                lang=request.lang,
                state={
                    "app": app_name,
                },
            )

            yield out(projection)
            return

        app_id = app["id"]

        # already active
        if app_id == self.on_get_active_app():
            projection = await self.on_project(
                key="use:using",
                scope="shell",
                lang=request.lang,
                state={
                    "app": app,
                },
            )

            yield out(projection)
            return

        # activate
        self.on_set_active_app(app_id=app_id)
        await self.on_save_session()
        yield out(to_text(f"Aktiver Kontext: {app_name}"))


# ----------------------------------
# PORTS
# ----------------------------------


class OnSaveSession(Protocol):

    async def __call__(
        self,
    ) -> None: ...


class OnGetActiveApp(Protocol):

    def __call__(
        self,
    ) -> str | None: ...


class OnSetActiveApp(Protocol):

    def __call__(
        self,
        *,
        app_id: str,
    ) -> None: ...
