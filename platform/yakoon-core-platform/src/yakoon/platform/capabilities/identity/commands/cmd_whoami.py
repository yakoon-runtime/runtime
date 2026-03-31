from yakoon.base.commands import Command, Request
from yakoon.base.flow import present


class CmdWhoAmI(Command):

    key = "whoami"

    async def run(self, request: Request):

        projector = await self.create_projector()

        username = self.ctx.session.get_username()
        if username:
            projection = await projector.project("show_user", user=username)
        else:
            projection = await projector.project("show_hint")

        yield present(projection)
