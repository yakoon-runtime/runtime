from yakoon.base.runtime import Command, Request, Session


class CmdQuit(Command):

    key = "quit"

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        presenter = await self.get_presenter(session)
        result = await presenter.present("really_quit")
        if bool(result and result.first()):
            session.signal("exit_app")
