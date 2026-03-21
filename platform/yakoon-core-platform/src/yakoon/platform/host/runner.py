from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.engine import CommandDispatch
from yakoon.base.host.events import InputEvent
from yakoon.base.runtime import Session
from yakoon.base.runtime.sessions.flow import FlowState
from yakoon.platform.engine import CommandEngine
from yakoon.platform.host.scheduler import Scheduler


@dataclass
class Runner:
    engine: CommandEngine
    session: Session
    scheduler: Scheduler

    async def on_input(self, event: InputEvent):

        flow = self.session.flow

        # Kontext entscheidet
        if flow and flow.state == FlowState.WAITING_INPUT:
            data = event.to_values()
            self.scheduler.resume_input(self.session, data)
            return

        data = event.to_text()
        await self.engine.dispatch(self.session, CommandDispatch(data))
        self.scheduler.schedule(self.session)
