from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from yakoon.base.engine import CommandDispatch, CommandQueueService, FlowState
from yakoon.base.host import Interaction
from yakoon.base.runtime import Session
from yakoon.base.runtime.commands.steps.outcome import AwaitInput
from yakoon.base.ui import ViewSpec
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

            flow = self.session.flow

            # ---------------------------------
            # 1. Aktiver Flow
            # ---------------------------------
            if flow:

                # Sleep prüfen
                if not should_wake(flow):
                    await asyncio.sleep(0.05)
                    continue

                flow.pop("wake_at", None)

                result = await self.engine.tick(self.session)

                # ---------------------------------
                # WAITING
                # ---------------------------------
                if result.state == FlowState.WAITING:

                    outcome = result.outcome

                    # Input erforderlich
                    if isinstance(outcome, AwaitInput):

                        view = ViewSpec("view", blocks=[outcome.block])

                        await self.interaction.prompt(
                            ps1="",
                            view=view,
                        )
                        return

                    # Sleep oder andere WAIT-Zustände
                    continue

                # ---------------------------------
                # FINISHED → Flow beenden
                # ---------------------------------
                if result.state == FlowState.FINISHED:
                    self.session.flow = None
                    continue

                # ---------------------------------
                # RUNNING → weiter treiben
                # ---------------------------------
                continue

            # ---------------------------------
            # 2. Exit
            # ---------------------------------
            if self.session.has_mark("exit_app"):
                await self.interaction.exit()
                return

            # ---------------------------------
            # 3. CommandQueue
            # ---------------------------------
            queue = self.engine.services.get(CommandQueueService)
            di = queue.next_input(self.session)

            if di:
                await self.engine.dispatch(self.session, di)
                continue

            # ---------------------------------
            # 4. Idle → Prompt anzeigen
            # ---------------------------------
            ps1 = format_ps1(self.session)

            await self.interaction.ready(ps1=ps1)
            return


def now():
    return time.time()


def should_wake(flow):
    wake_at = flow.get("wake_at")
    return wake_at is None or wake_at <= now()
