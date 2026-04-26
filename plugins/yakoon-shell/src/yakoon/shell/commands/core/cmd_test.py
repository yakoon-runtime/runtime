from yakoon.base.commands import Command, Request
from yakoon.base.flow import out
from yakoon.base.projection.model.block import TextBlock
from yakoon.base.projection.model.model import Projection

# from yakoon.base.flow import present


class CmdTest(Command):

    key = "test"

    async def run(self, request: Request):

        # operation = request.arg(0)
        # print(operation)

        yield out(value=self.create_data("Stefan"))
        yield out(value=self.create_data("Bob"))
        yield out(value=self.create_data("Mike"))

        # yield Outcome(value={"user_name": "Bob"})
        # yield Outcome(value={"user_name": "Mike"})

        # projector = await self.create_projector()
        # projection = await projector.project("ask1")
        # yield present(projection)

    def create_data(self, name: str):
        return Projection.create(
            blocks=[
                TextBlock.create(text=name),
            ]
        )
