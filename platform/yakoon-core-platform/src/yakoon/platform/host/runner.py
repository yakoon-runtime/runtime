from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.engine import CommandDispatch
from yakoon.base.host import Interaction
from yakoon.base.runtime import Session
from yakoon.platform.engine import CommandEngine
from yakoon.platform.host.scheduler import Scheduler


@dataclass
class Runner:
    engine: CommandEngine
    session: Session
    interaction: Interaction
    scheduler: Scheduler

    async def on_user_input(self, text: str):
        await self.engine.dispatch(self.session, CommandDispatch(text=text))
        self.scheduler.schedule(self.session)

    async def on_input_submit(self, values):
        self.scheduler.resume_input(self.session, values)
