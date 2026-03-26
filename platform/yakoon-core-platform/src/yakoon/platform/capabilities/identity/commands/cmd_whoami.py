from yakoon.base.runtime.commands import Command, Request


class CmdWhoAmI(Command):

    key = "whoami"

    async def run(self, request: Request) -> None:  # noqa: ARG002

        presenter = await self.get_presenter(session)

        username = session.get_username()
        if username:
            await presenter.present("show_user", user=username)
        else:
            await presenter.present("show_hint")
