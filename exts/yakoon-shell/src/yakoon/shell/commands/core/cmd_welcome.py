from yakoon.base.commands import Command, Request
from yakoon.base.flow import show


class CmdWelcome(Command):

    key = "welcome"

    async def run(self, request: Request):

        presenter = await self.get_presenter()
        view = await presenter.render("show")
        yield show(view)
