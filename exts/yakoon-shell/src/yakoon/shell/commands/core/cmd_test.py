from yakoon.base.capabilities.interaction import PolicyService
from yakoon.base.runtime import Command, Request, Session
from yakoon.base.runtime.commands import (
    Advance,
    CommandFlow,
    CommandKind,
    CommandVisibility,
    Delay,
    compile_view,
)
from yakoon.base.ui import v_text


class CmdTest(Command):

    key = "test"
    kind = CommandKind.BUILTIN
    visibility = CommandVisibility.DEVELOPER

    async def run(self, session: Session, request: Request) -> CommandFlow:

        policy = self.services.get(PolicyService)
        presenter = await self.get_presenter(session=session)

        view = await presenter.view("ask1")
        view_group = presenter.group_blocks_by_type(view)
        async for step in compile_view(
            view.id, view.header, groups=view_group, policy_service=policy
        ):
            result = yield step
            pass

    async def _run_delay(self, session: Session, request: Request) -> CommandFlow:

        while True:

            # 1. Ausgabe
            await session.emit(v_text("\nHello"))

            # 2. 5 Sekunden warten
            yield Delay(3)

    async def _run_print_message(
        self, session: Session, request: Request
    ) -> CommandFlow:
        messages = ["Test print..."]
        await session.emit(v_text(str(messages)))
        yield Advance()

    async def __run(self, session: Session, request: Request) -> CommandFlow:

        messages = ["Test print..."]
        await session.emit(v_text(str(messages)))
        yield Advance()

        policy = self.services.get(PolicyService)
        presenter = await self.get_presenter(session=session)

        view = await presenter.view("ask1")
        view_group = presenter.group_blocks_by_type(view)
        for i, group in enumerate(view_group):
            async for step in compile_view(group, policy_service=policy):
                yield step

        # data = yield Ask("ask1", presenter)
        # messages.append(data)

        # data = yield Ask("ask1", presenter)
        # messages.append(data)

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

        result = await self.ask(session, "ask1")
        await session.emit(v_text(result.first()))

        result = await self.ask(session, "ask2")
        await session.emit(v_text(result.get("result")))

        result = await self.ask(session, "ask3")
        await session.emit(v_text(result.get("the_key")))

        presenter = await self.get_presenter(session)
        items = await presenter.present("ask4")
        if items:
            for item in items.list():
                await session.emit(v_text(item))
