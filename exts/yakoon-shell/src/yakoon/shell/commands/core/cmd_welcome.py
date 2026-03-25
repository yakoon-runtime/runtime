from yakoon.base.api import Command, Request


class CmdWelcome(Command):

    key = "welcome"

    async def run(self, request: Request) -> None:  # noqa: ARG002

        presenter = await self.get_presenter()
        await presenter.present("show")
