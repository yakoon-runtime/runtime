from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.engine import CommandDispatch
from yakoon.base.host import InputEvent
from yakoon.base.runtime import Session
from yakoon.platform.engine import CommandEngine
from yakoon.platform.host.scheduler import Scheduler


@dataclass
class Runner:
    engine: CommandEngine
    session: Session
    scheduler: Scheduler

    async def on_input(self, event: InputEvent):

        flow = self.session.focused_flow

        # Wenn Flow aktiv → Event direkt rein
        if flow:
            self.session.send_event(event)
            self.scheduler.schedule_flow(flow, self.session)
            return

        # Nur Fallback interpretiert Text
        text = event.to_text()
        await self.scheduler.dispatch(self.session, CommandDispatch(text))
