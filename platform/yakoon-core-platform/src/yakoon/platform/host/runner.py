from __future__ import annotations

import time
from dataclasses import dataclass

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

    async def start(self, commands: list[str] | None = None) -> None:
        if commands:
            queue = self.engine.services.get(CommandQueueService)
            queue.enqueue_commands(self.session, commands)

        await self.run()

    async def on_user_input(self, text: str) -> None:
        await self.engine.dispatch(self.session, CommandDispatch(text=text))
        await self.run()

    async def on_input_submit(self, values: dict[str, object]) -> None:
        self.session.flow["input"] = values
        await self.run()

    async def run(self) -> None:

        while True:

            # 1. Flow aktiv → treiben
            if self.session.flow:
                result = await self.engine.tick(self.session)

                if result.state == FlowState.WAITING:
                    await self.interaction.prompt(
                        ps1="",
                        view=result.outcome.view,
                    )
                    return

                if result.state == FlowState.FINISHED:
                    # Flow ist weg → direkt weiter
                    continue

                # RUNNING → weiter treiben
                continue

            # 2. Exit
            if self.session.has_mark("exit_app"):
                await self.interaction.exit()
                return

            # 3. CommandQueue prüfen
            queue = self.engine.services.get(CommandQueueService)
            di = queue.next_input(self.session)

            if di:
                await self.engine.dispatch(self.session, di)
                continue

            # 💤 4. Idle → Prompt anzeigen
            ps1 = format_ps1(self.session)

            await self.interaction.ready(ps1=ps1)
            return


def now():
    return time.time()


def should_wake(flow):
    wake_at = flow.get("wake_at")
    return wake_at is None or wake_at <= now()
