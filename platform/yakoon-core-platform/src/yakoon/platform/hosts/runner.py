from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.capabilities.interaction import DialogService
from yakoon.base.engine import CommandDispatch, CommandQueueService, ResolveDispatch
from yakoon.base.runtime.sessions.session import Session
from yakoon.platform.engine import CommandEngine
from yakoon.platform.hosts.adapter import HostAdapter
from yakoon.platform.hosts.format import format_ps1


@dataclass
class Runner:
    engine: CommandEngine
    session: Session
    host: HostAdapter

    async def start(self, commands: list[str] | None = None) -> None:
        await self.drive(commands=commands)

    async def on_user_input(self, text: str) -> None:
        await self.engine.dispatch(self.session, CommandDispatch(text=text))
        await self.drive()

    async def on_input_submit(self, values: dict[str, object]) -> None:
        await self.engine.dispatch(self.session, ResolveDispatch(values=values))
        await self.drive()

    async def on_cancel(self) -> None:
        await self.engine.dispatch(self.session, CommandDispatch("shell:wf.cancel"))
        await self.drive()

    async def drive(self, *, commands: list[str] | None = None) -> None:
        dialogs = self.engine.services.get(DialogService)
        queue = self.engine.services.get(CommandQueueService)

        if commands:
            queue.enqueue_commands(self.session, commands)

        while True:
            if self.session.has_signal("exit_app"):
                await self.host.on_exit()
                return

            ps1 = format_ps1(self.session)

            if dialogs.is_waiting(self.session):
                view = dialogs.get_view(self.session)
                await self.host.on_view(ps1=ps1, view=view)
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
