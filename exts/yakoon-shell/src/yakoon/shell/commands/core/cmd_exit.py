from yakoon.base.commands.command import Command
from yakoon.base.commands.request import Request
from yakoon.base.models.command import CommandScope
from yakoon.base.ports import ControllerCatalogService, SessionService
from yakoon.base.runtime.session import Session


class CmdExit(Command):

    key = "exit"
    scope = CommandScope.GLOBAL

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        controllers = self.services.get(ControllerCatalogService)

        shell = controllers.shell()[0]
        active_controller_id = session.get_active_controller()
        if shell.id != active_controller_id:
            session.set_active_controller(shell.id)
            await self.services.get(SessionService).save(session)
