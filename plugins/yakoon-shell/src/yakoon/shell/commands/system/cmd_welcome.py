from yakoon.base.commands import Command, Request
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.flow import out


class CmdWelcome(Command):

    key = "welcome"

    def __init__(self, on_project: OnProjectCmd):
        self.on_project = on_project

    async def run(self, request: Request):

        projection = await self.on_project(
            name="result.sam",
            state={"name": request.payload},
        )

        yield out(projection)
