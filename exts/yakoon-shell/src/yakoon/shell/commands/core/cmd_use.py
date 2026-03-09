from yakoon.base.catalogs import ControllerCatalogService
from yakoon.base.runtime import Command, Request, Session, SessionService


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
            await presenter.present("show", controllers=infos)
        elif infos:
            if name == session.get_active_controller():
                await presenter.present("already_in_shell", controller=infos[0])
            else:
                session.set_active_controller(name)
                await self.services.get(SessionService).save(session)
        else:
            await presenter.present("name_not_found", name=name)
