from yakoon.base.runtime import Command, Request, Session
from yakoon.base.runtime.commands import CommandKind, CommandVisibility
from yakoon.base.ui.views import v_text


class CmdTest(Command):

    key = "test"
    kind = CommandKind.BUILTIN
    visibility = CommandVisibility.DEVELOPER

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        presenter = await self.get_presenter(session)
        result = await presenter.present("ask1")
        if result:
            await session.emit(v_text(f" -> {result.first()}"))

        result = await presenter.present("ask2")
        if result:
            await session.emit(v_text(result.get("result")))

        result = await presenter.present("ask3")
        if result:
            await session.emit(v_text(result.get("the_key")))

        items = await presenter.present("ask4")
        if items:
            for item in items.list():
                await session.emit(v_text(item))
