from y5n.base.commands import Command, Request
from y5n.base.flow import receive
from y5n.base.flow.patterns import form, write_text


class CmdDemoFormSelect(Command):

    key = "demo.form.select"

    async def run(self, request: Request):

        projector = await self.create_projector()
        projection = await projector.project("view_1")

        yield form(self, projection, "channel_a")
        event = yield receive("channel_a")

        values = event.to_values()
        yield write_text(f"Ihre Eingabe: {values}")
