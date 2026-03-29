from typing import Protocol, cast

from yakoon.base.catalogs import ControllerCatalogService
from yakoon.base.commands import (
    Command,
    CommandScope,
    Request,
)
from yakoon.base.flow import text
from yakoon.base.runtime.sessions.port import SessionService


class _ControllerAccess(Protocol):
    def get_active_controller(self) -> str: ...
    def set_active_controller(self, controller_id: str) -> None: ...
    def set_interaction(self, flow_id: str | None): ...
    def has_interaction(self) -> bool: ...


class CmdExit(Command):

    key = "exit"
    scope = CommandScope.GLOBAL

    async def run(self, request: Request):

        sys_session = self.context.session
        # privileged access: controller management
        access = cast(_ControllerAccess, sys_session)

        # 1. Fokus verlassen (höchste Priorität)
        # --------------------------------------------------
        if access.has_interaction():
            access.set_interaction(None)
            yield text("↩ Fokus verlassen")
            return

        # --------------------------------------------------
        # 2. Controller verlassen
        # --------------------------------------------------
        controllers = self.services.get(ControllerCatalogService)
        shell = controllers.shell()[0]

        current = access.get_active_controller()

        if shell.id != current:
            access.set_active_controller(shell.id)
            await self.services.get(SessionService).save(sys_session)
            current = shell.id

        yield text(f"Kontroller: {current}")
