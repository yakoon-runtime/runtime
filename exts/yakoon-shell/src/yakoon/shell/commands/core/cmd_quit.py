from typing import Protocol, cast

from yakoon.base.commands import Command, Request
from yakoon.base.flow.patterns import form


class _SessionMarkAccess(Protocol):
    def mark(self, name: str): ...


class CmdQuit(Command):

    key = "quit"

    async def run(self, request: Request):

        presenter = await self.get_presenter()
        view = await presenter.render("really_quit")

        result = yield form(view, self.services)

        answer = bool(result.values.get("quit"))
        if answer:
            access = cast(_SessionMarkAccess, self.ctx.session)
            access.mark("exit_app")

        # yield write("END.")
