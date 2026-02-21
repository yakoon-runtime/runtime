from yakoon.base.commands.command import Command
from yakoon.base.commands.request import Request
from yakoon.base.ports import ControllerCatalogService, SessionService
from yakoon.base.runtime.session import Session


class CmdUse(Command):

    key = "use"

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        controllers = self.services.get(ControllerCatalogService)
        presenter = await self.get_presenter(session)

        infos = []
        name = request.arg(0)
        if not name:
            infos = controllers.all()
        else:
            controller = controllers.get(name)
            if controller:
                infos.append(controller)

        if infos and not name:
            await presenter.views.emit("show", controllers=infos)
        elif infos:
            if name == session.get_active_controller():
                await presenter.views.emit("already_in_shell", controller=infos[0])
            else:
                session.set_active_controller(name)
                await self.services.get(SessionService).save(session)
        else:
            await presenter.views.emit("name_not_found", name=name)
