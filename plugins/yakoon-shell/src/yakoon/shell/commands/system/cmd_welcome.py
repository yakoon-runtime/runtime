from yakoon.base.commands import Command, Invocation, Request
from yakoon.base.flow import out
from yakoon.base.plugins.ports import OnProject


class CmdWelcome(Command):

    key = "welcome"
    anonymous = True

    invocations = [
        Invocation(),
    ]

    def __init__(self, on_project: OnProject):
        self.on_project = on_project

    async def run(self, request: Request):

        projection = await self.on_project(
            key="welcome:result",
            scope="shell",
            lang=request.lang,
            state={"name": request.payload},
        )

        yield out(projection)
