from y5n.base.commands import Command, Request
from y5n.base.flow.dsl import prompt, receive
from y5n.base.flow.patterns import out_text


class CmdDemoSubflow(Command):

    key = "demo.subflow.simple"

    async def run(self, request: Request):

        yield out_text("\nA start")
        yield self.sub()

        yield out_text("\nA end")
        yield out_text("\nA start again")

        yield self.sub()
        yield out_text("\nA end again")

    async def sub(self):

        projector = await self.create_projector()
        projection = await projector.project("view_1")

        yield out_text("\nB start")
        yield prompt(projection)

        value = yield receive()
        yield out_text("\n" + f"B got {value}")


# name = (yield ask(view1)).require("name")
# age  = (yield ask(view2)).require("age")
