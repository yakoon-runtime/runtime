from yakoon.base.catalogs import ControllerCatalogService
from yakoon.base.runtime.commands import Command, Request
from yakoon.base.runtime.flow import show
from yakoon.base.runtime.sessions import SessionService


class CmdUse(Command):

    key = "use"

    async def run(self, request: Request):

        session = self.context.session
        controllers = self.services.get(ControllerCatalogService)
        presenter = await self.get_presenter()

        infos = []
        name = request.arg(0)
        if not name:
            infos = controllers.all()
        else:
            controller = controllers.get(name)
            if controller:
                infos.append(controller)

        if infos and not name:
            result = await presenter.render("show", controllers=infos)
            yield show(result.view)
        elif infos:
            # internes Protocol verwenden.
            if name == session.get_active_controller():
                result = await presenter.render("already_in_shell", controller=infos[0])
                yield show(result.view)
            else:
                session.set_active_controller(name)
                await self.services.get(SessionService).save(session)
        else:
            result = await presenter.render("name_not_found", name=name)
            yield show(result.view)
