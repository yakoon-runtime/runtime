from yakoon.base.runtime import Command, Request, Session
from yakoon.base.runtime.commands import CommandKind, CommandVisibility
from yakoon.base.ui.views import v_text


class CmdTest(Command):

    key = "test"
    kind = CommandKind.BUILTIN
    visibility = CommandVisibility.DEVELOPER

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        presenter = await self.get_presenter(session)
        result = await presenter.inputs.ask("ask1")
        await session.emit(v_text(f" -> {result.first()}"))

        result = await presenter.inputs.ask("ask2")
        await session.emit(v_text(result.get("result")))

        result = await presenter.inputs.ask("ask3")
        await session.emit(v_text(result.get("the_key")))

        items = await presenter.inputs.ask("ask4")
        for item in items.list():
            await session.emit(v_text(item))
