from yakoon.base.commands.command import Command
from yakoon.base.commands.request import Request
from yakoon.base.runtime.session import Session


class CmdQuit(Command):

    key = "quit"

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        presenter = await self.get_presenter(session)
        result = await presenter.inputs.ask("really_quit")
        if bool(result.first()):
            session.signal("exit_app")
