from yakoon.base.commands import Command, Request
from yakoon.base.flow import present


class CmdTestCity(Command):

    key = "city.show.all"

    async def run(self, request: Request):

        projector = await self.create_projector()
        projection = await projector.project("show")
        yield present(projection)
