from yakoon.base.runtime import Command, Request, Session


class CmdWelcome(Command):

    key = "welcome"

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        presenter = await self.get_presenter(session)
        await presenter.present("show")
