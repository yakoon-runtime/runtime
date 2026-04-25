from typing import Protocol, cast

from yakoon.base.commands import Command, Request
from yakoon.base.flow import present
from yakoon.base.flow.patterns import write_text
from yakoon.base.runtime.sessions import SessionStore


class _ControllerAccess(Protocol):
    def get_active_app(self) -> str: ...
    def set_active_app(self, name: str) -> None: ...


class CmdUse(Command):

    key = "use"

    async def run(self, request: Request):

        applications = []
        session = self.ctx.session
        projector = await self.create_projector()
        access = cast(_ControllerAccess, session)

        app_query = self.container.get(ApplicationQuery)

        name = request.arg(0)
        if not name:
            applications = app_query.all()
        else:
            app = app_query.get(name)
            if app:
                applications.append(app)

        if applications and not name:
            projection = await projector.project(
                "active",
                state={
                    "apps": applications,
                },
            )
            yield present(projection)

        elif applications:
            if name == access.get_active_app():
                projection = await projector.project(
                    "using",
                    state={
                        "app": applications[0],
                    },
                )
                yield present(projection)
            else:
                access.set_active_app(name)
                await self.container.get(SessionStore).save(session)
                yield write_text(f"Aktiver Kontext: {name}")

        else:
            projector = await projector.project(
                "error",
                state={
                    "app": name,
                },
            )
            yield present(projector)
