from yakoon.base.commands.command import Command
from yakoon.base.commands.request import Request
from yakoon.base.runtime.session import Session


class CmdWhoAmI(Command):

    key = "whoami"

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        presenter = await self.get_presenter(session)

        username = session.get_username()
        if username:
            await presenter.views.emit("show_user", user=username)
        else:
            await presenter.views.emit("show_hint")
