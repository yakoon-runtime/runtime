from y5n.base.commands import Command, Request
from y5n.base.flow import prompt, receive
from y5n.base.flow.patterns import out_text
from y5n.base.flow.patterns.internal.validate import apply_errors, validate


class CmdDemoValidateSimple(Command):

    key = "demo.validate.simple"

    async def run(self, request: Request):

        projector = await self.create_projector()
        projection = await projector.project("view_1")

        while True:
            yield prompt(projection)

            event = yield receive()

            result = validate(projection, event, self.container)
            if not result.ok:
                projection = apply_errors(projection, result.errors)
                continue

            values = result.values
            yield out_text(f"Ihre Eingabe: {values}")
            break
