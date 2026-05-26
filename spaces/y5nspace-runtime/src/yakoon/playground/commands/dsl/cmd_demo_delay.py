from y5n.base.commands import Command, Request
from y5n.base.flow import delay
from y5n.base.flow.patterns import write_text


class CmdDemoDelaySimple(Command):

    key = "demo.delay.simple"

    async def run(self, request: Request):

        yield write_text("Start")

        yield delay(5)

        yield write_text("\nDone")
