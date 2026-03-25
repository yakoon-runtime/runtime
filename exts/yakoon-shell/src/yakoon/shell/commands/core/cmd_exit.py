from yakoon.base.api import Command, Request
from yakoon.base.api.command import CommandScope
from yakoon.base.catalogs import ControllerCatalogService
from yakoon.base.runtime.sessions.port import SessionService


class CmdExit(Command):

    key = "exit"
    scope = CommandScope.GLOBAL

    async def run(self, request: Request):

        controllers = self.services.get(ControllerCatalogService)

        shell = controllers.shell()[0]
        sysession = self.context.system
        active_controller_id = sysession.get_active_controller()
        if shell.id != active_controller_id:
            sysession.set_active_controller(shell.id)
            await self.services.get(SessionService).save(sysession)
