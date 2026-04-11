from typing import Protocol, cast

from yakoon.base.commands import Command, Request
from yakoon.base.flow import receive
from yakoon.base.flow.patterns import form


class _SessionMarkAccess(Protocol):
    def mark(self, name: str): ...


class CmdQuit(Command):

    key = "quit"

    async def run(self, request: Request):

        projector = await self.create_projector()
        projection = await projector.project("confirm")

        yield form(self, projection, "form")

        result = yield receive("form")

        answer = bool(result.values.get("quit"))
        if answer:
            access = cast(_SessionMarkAccess, self.ctx.session)
            access.mark("exit_app")
