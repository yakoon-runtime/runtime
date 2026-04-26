from yakoon.base.commands import Command, Request
from yakoon.base.flow import out


class CmdWelcome(Command):

    key = "welcome"

    async def run(self, request: Request):

        projection = await self.on_project(
            name="result.sam", state={"name": request.payload}
        )
        yield out(projection)
