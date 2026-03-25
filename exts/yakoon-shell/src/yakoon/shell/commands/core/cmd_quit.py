from yakoon.base.api import Command, Request, ask
from yakoon.base.capabilities.interaction.port import PolicyService


class CmdQuit(Command):

    key = "quit"

    async def run(self, request: Request):

        presenter = await self.get_presenter()
        policy = self.services.get(PolicyService)
        view = await presenter.render("really_quit")

        ask(view, policies)
        result = await presenter.require_present("really_quit")
        if result.cancelled:
            return
            # print("test")

        if bool(result and result.first()):
            session.mark("exit_app")
