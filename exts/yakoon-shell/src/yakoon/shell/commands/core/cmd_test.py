from yakoon.base.commands.command import Command
from yakoon.base.commands.request import Request
from yakoon.base.models.command import CommandKind, CommandVisibility
from yakoon.base.runtime.session import Session
from yakoon.base.runtime.session.views import v_text


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
