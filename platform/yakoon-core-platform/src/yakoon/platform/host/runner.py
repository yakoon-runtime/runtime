from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.engine import CommandDispatch
from yakoon.base.runtime import Session
from yakoon.base.runtime.sessions.flow import FlowState
from yakoon.platform.engine import CommandEngine
from yakoon.platform.host.scheduler import Scheduler


@dataclass
class Runner:
    engine: CommandEngine
    session: Session
    scheduler: Scheduler

    async def on_input(self, event):

        flow = self.session.flow

        # Kontext entscheidet
        if flow and flow.state == FlowState.WAITING_INPUT:
            self.scheduler.resume_input(self.session, event.value)
            return

        await self.engine.dispatch(
            self.session,
            CommandDispatch(event.value),
        )
        self.scheduler.schedule(self.session)
