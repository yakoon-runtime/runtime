from yakoon.base.runtime.commands import Command, Request


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
