from yakoon.base.commands import Command, Request
from yakoon.base.flow import present


class CmdWelcome(Command):

    key = "welcome"

    async def run(self, request: Request):

        projection = await self.on_project(
            name="result.sam", state={"name": request.payload}
        )
        yield present(projection)
