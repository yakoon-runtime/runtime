from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.engine import CommandDispatch
from yakoon.base.runtime.flow import FlowState
from yakoon.base.runtime.input import InputEvent
from yakoon.base.runtime.sessions import Session
from yakoon.platform.engine import CommandEngine
from yakoon.platform.host.scheduler import Scheduler


@dataclass
class Runner:
    engine: CommandEngine
    session: Session
    scheduler: Scheduler

    async def on_input(self, event: InputEvent):

        flow = self.session.focused_flow

        # --------------------------------------------------
        # 1. Kein Flow → Command Dispatch
        # --------------------------------------------------
        if not flow:
            text = event.to_text()
            await self.scheduler.dispatch(self.session, CommandDispatch(text))
            return

        # --------------------------------------------------
        # 2. Flow wartet auf InputStep (Ask/Form)
        # --------------------------------------------------
        if flow.state == FlowState.WAITING_INPUT:
            self.scheduler.resume_input(self.session, event)
            return

        # --------------------------------------------------
        # 3. Normaler Flow → Event (Receive)
        # --------------------------------------------------
        self.session.send_event(event)
        self.scheduler.schedule_flow(flow, self.session)
