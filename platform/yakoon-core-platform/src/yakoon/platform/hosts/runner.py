from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.capabilities.interaction import DialogService
from yakoon.base.engine import CommandDispatch, CommandQueueService, ResolveDispatch
from yakoon.base.runtime import Session
from yakoon.platform.engine import CommandEngine

from . import HostAdapter, Interaction, format_ps1


@dataclass
class Runner:
    engine: CommandEngine
    session: Session
    host: HostAdapter
    interact: Interaction

    async def start(self, commands: list[str] | None = None) -> None:
        await self.drive(commands=commands)

    async def on_user_input(self, text: str) -> None:
        await self.engine.dispatch(self.session, CommandDispatch(text=text))

        if self.interact:
            entry = self.session.execution.resolved_entry()
            if entry and entry.command:
                self.interact.add_history(entry.command)

        await self.drive()

    async def on_input_submit(self, values: dict[str, object]) -> None:
        await self.engine.dispatch(self.session, ResolveDispatch(values=values))
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
        dialogs = self.engine.services.get(DialogService)
        queue = self.engine.services.get(CommandQueueService)

        if commands:
            queue.enqueue_commands(self.session, commands)

        while True:

            if self.session.has_mark("exit_app"):
                await self.host.on_exit()
                return

            ps1 = format_ps1(self.session)

            if dialogs.is_waiting(self.session):

                # print("wait_ready ---------------- START")
                await self.session.wait_ready()
                # print("wait_ready ------------------ END")

                view = dialogs.get_view(self.session)
                await self.host.on_prompt(ps1=ps1, view=view)
                return

            # Drain queued command handling
            di = queue.next_input(self.session)
            if di:
                await self.engine.dispatch(self.session, di)
                continue

            if hasattr(self.host, "on_ready"):
                await self.host.on_ready(ps1=ps1)
            else:
                await self.host.on_idle()
