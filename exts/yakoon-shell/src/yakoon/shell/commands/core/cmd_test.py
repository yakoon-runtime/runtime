from yakoon.base.commands import Command, Request
from yakoon.base.flow import present


class CmdTest(Command):

    key = "test"

    async def run(self, request: Request):

        projector = await self.create_projector()
        projection = await projector.project("ask1")
        yield present(projection)
