from yakoon.base.runtime import Command, Request, Session


class CmdWhoAmI(Command):

    key = "whoami"

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        presenter = await self.get_presenter(session)

        username = session.get_username()
        if username:
            await presenter.views.emit("show_user", user=username)
        else:
            await presenter.views.emit("show_hint")
