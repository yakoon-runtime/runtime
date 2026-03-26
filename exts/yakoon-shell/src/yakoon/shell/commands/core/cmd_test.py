from yakoon.base.capabilities.interaction import PolicyService
from yakoon.base.runtime.commands import (
    Command,
    CommandKind,
    CommandVisibility,
    Request,
)
from yakoon.base.runtime.flow import compile_view
from yakoon.base.runtime.input import InputEvent
from yakoon.base.runtime.steps.step import InputStep
from yakoon.base.ui import v_text
from yakoon.platform.runtime import DomainError


class CmdTest(Command):

    key = "test"
    kind = CommandKind.BUILTIN
    visibility = CommandVisibility.DEVELOPER

    async def run(self, request: Request):

        policy = self.services.get(PolicyService)
        presenter = await self.get_presenter(session=session)

        view = await presenter.view("ask2")
        async for step in compile_view(
            view.id, view.header, groups=view.groups(), policy_service=policy
        ):

            while True:
                try:
                    event: InputEvent = yield step
                    if isinstance(step, InputStep):

                        value = event.get("result", 0)

                        if value > 10:
                            raise DomainError(
                                "\nKunde nicht gefunden", "customer_not_found"
                            )

                        if value == 7:
                            yield step.reject("result", "Nicht die 7")
                            continue

                    # alle andere steps
                    break

                except DomainError:
                    raise
                    # continue

    async def wait_run(self, request: Request):

        name = str(request.args)
        await session.emit(v_text(f"Hello started ... {name}"))
        while True:

            event: InputEvent = yield Receive(wait=True)
            name = event.to_text()
            await session.emit(v_text(f"Hello {name}"))

            yield Delay(5)

    async def delay_run(self, request: Request):

        yield Show(v_text("\nStart"))
        yield Delay(10)
        yield Show(v_text("\nDone"))

    async def __run(self, request: Request):

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

    async def _run(self, request: Request):  # noqa: ARG002

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
