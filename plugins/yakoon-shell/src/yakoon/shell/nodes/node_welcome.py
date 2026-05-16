from yakoon.base.commands import Command, Invocation, Request
from yakoon.base.flow import out
from yakoon.base.nodes import RuntimeContext
from yakoon.base.plugins.ports import OnProject
from yakoon.base.projection import to_text

# command new


async def run_welcome(ctx: RuntimeContext):
    """projection = await ctx.port(OnProject)(
        key="welcome:result",
        scope="shell",
        lang=ctx.request.lang,
        state={"name": ctx.request.payload},
    )"""

    projection = to_text("Hello world")
    yield out(projection)


# Command before


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
