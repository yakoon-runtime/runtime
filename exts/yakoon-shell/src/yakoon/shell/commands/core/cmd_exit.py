from typing import Protocol, cast

from yakoon.base.catalogs import ControllerCatalogService
from yakoon.base.flow import text
from yakoon.base.runtime.commands import (
    Command,
    CommandScope,
    Request,
)
from yakoon.base.runtime.sessions.port import SessionService


class _ControllerAccess(Protocol):
    def get_active_controller(self) -> str: ...
    def set_active_controller(self, controller_id: str) -> None: ...


class CmdExit(Command):

    key = "exit"
    scope = CommandScope.GLOBAL

    async def run(self, request: Request):

        sys_session = self.context.session
        # privileged access: controller management
        access = cast(_ControllerAccess, sys_session)

        controllers = self.services.get(ControllerCatalogService)
        shell = controllers.shell()[0]

        current = access.get_active_controller()

        if shell.id != current:
            access.set_active_controller(shell.id)
            await self.services.get(SessionService).save(sys_session)
            current = shell.id

        yield text(f"Kontroller: {current}")
