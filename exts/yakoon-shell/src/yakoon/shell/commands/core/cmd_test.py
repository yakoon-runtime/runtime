from collections.abc import AsyncGenerator

from yakoon.base.engine.step import Ask, Step
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

    async def run(
        self, session: Session, request: Request
    ) -> AsyncGenerator[Step, None]:

        messages = []

        presenter = await self.get_presenter(session=session)
        data = yield Ask("ask1", presenter)
        messages.append(data)

        data = yield Ask("ask1", presenter)
        messages.append(data)

        await session.emit(v_text(str(messages)))

        # view = await presenter.view("ask1")

        # yield Show("ask1", presenter)
        # data = yield Ask("ask1", presenter)

        # compiled = compile_view(view)
        # async for step in compiled(self, session, request):
        #    yield step

        # data = yield Ask("ask1", presenter)

        # print(data)

    async def _run(self, session: Session, request: Request) -> None:  # noqa: ARG002

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
