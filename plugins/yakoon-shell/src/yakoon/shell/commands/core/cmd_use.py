from typing import Protocol, cast

from yakoon.base.catalogs import ControllerRegistry
from yakoon.base.commands import Command, Request
from yakoon.base.flow import present
from yakoon.base.flow.patterns import write_text
from yakoon.base.runtime.sessions import SessionStore


class _ControllerAccess(Protocol):
    def get_active_controller(self) -> str: ...
    def set_active_controller(self, name: str) -> None: ...


class CmdUse(Command):

    key = "use"

    async def run(self, request: Request):

        session = self.ctx.session
        controllers = self.container.get(ControllerRegistry)
        projector = await self.create_projector()
        access = cast(_ControllerAccess, session)

        infos = []
        name = request.arg(0)
        if not name:
            infos = controllers.all()
        else:
            controller = controllers.get(name)
            if controller:
                infos.append(controller)

        if infos and not name:
            projection = await projector.project(
                "active",
                state={
                    "controllers": infos,
                },
            )
            yield present(projection)
        elif infos:

            if name == access.get_active_controller():
                projection = await projector.project(
                    "using",
                    state={
                        "controller": infos[0],
                    },
                )
                yield present(projection)
            else:
                access.set_active_controller(name)
                await self.container.get(SessionStore).save(session)
                yield write_text(f"Aktiver Kontroller: {name}")

        else:
            projector = await projector.project(
                "error",
                state={
                    "prg_name": name,
                },
            )
            yield present(projector)
