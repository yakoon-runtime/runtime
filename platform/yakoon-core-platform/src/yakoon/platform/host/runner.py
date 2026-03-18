from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.capabilities.interaction import DialogService
from yakoon.base.engine import CommandDispatch, CommandQueueService
from yakoon.base.engine.step import FlowState
from yakoon.base.host import Interaction
from yakoon.base.runtime import Session
from yakoon.platform.engine import CommandEngine

from . import format_ps1


@dataclass
class Runner:
    engine: CommandEngine
    session: Session
    interaction: Interaction

    def __post_init__(self):
        self._driving = False

    async def start(self, commands: list[str] | None = None) -> None:
        await self.drive(commands=commands)

    async def on_user_input(self, text: str) -> None:
        await self.engine.dispatch(self.session, CommandDispatch(text=text))
        # await self._tick_loop()
        # entry = self.session.execution.resolved_entry()
        # if entry and entry.command:
        # self.interact.add_history(entry.command)
        await self.drive()

    async def on_input_submit(self, values: dict[str, object]) -> None:
        self.session.flow["ctx"].update(values)
        await self.drive()

    async def on_cancel(self) -> None:
        dialogs = self.engine.services.get(DialogService)
        if dialogs.is_waiting(self.session):
            dialogs.resolve_cancelled(self.session)
            # update ui state
            await self.drive()
            return

        await self.engine.dispatch(self.session, CommandDispatch("shell:wf.cancel"))
        await self.drive()

    async def drive(self, *, commands: list[str] | None = None) -> None:

        self._drive_requested = True

        # if self._driving:
        #    return

        self._driving = True

        try:
            while self._drive_requested:
                self._drive_requested = False
                await self._drive(commands=commands)
        finally:
            self._driving = False

    async def _drive(self, *, commands: list[str] | None = None):

        queue = self.engine.services.get(CommandQueueService)
        if commands:
            queue.enqueue_commands(self.session, commands)

        while True:

            # Flow zuerst treiben
            if self.session.flow:
                await self._tick_loop()
                continue

            if self.session.has_mark("exit_app"):
                await self.interaction.exit()
                return

            di = queue.next_input(self.session)
            if di:
                await self.engine.dispatch(self.session, di)
                continue

            ps1 = format_ps1(self.session)
            if hasattr(self.interaction, "ready"):
                await self.interaction.ready(ps1=ps1)
            else:
                await self.interaction.idle()

            return

    async def _tick_loop(self):

        while True:

            if not self.session.flow:
                return

            result = await self.engine.tick(self.session)

            if result.state == FlowState.WAITING:
                view = result.outcome.view
                await self.interaction.prompt(ps1="test", view=view)
                return

            if result.state == FlowState.FINISHED:
                return

            # RUNNING → weiter
            return
            # continue
