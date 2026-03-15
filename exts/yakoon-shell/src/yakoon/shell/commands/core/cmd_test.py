from yakoon.base.runtime import Command, Request, Session
from yakoon.base.runtime.commands import (
    CommandCancelled,
    CommandKind,
    CommandVisibility,
)
from yakoon.base.ui.views import v_text


class CmdTest(Command):

    key = "test"
    kind = CommandKind.BUILTIN
    visibility = CommandVisibility.DEVELOPER

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        try:
            result = await self.ask(session, "ask1")
            await session.emit(v_text(result.first()))

            result = await self.ask(session, "ask2")
            await session.emit(v_text(result.get("result")))

            result = await self.ask(session, "ask3")
            await session.emit(v_text(result.get("the_key")))
        except CommandCancelled:
            return

        presenter = await self.get_presenter(session)
        items = await presenter.present("ask4")
        if items:
            for item in items.list():
                await session.emit(v_text(item))
