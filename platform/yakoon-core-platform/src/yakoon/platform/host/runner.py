from __future__ import annotations

from yakoon.base.catalogs.port import CommandCatalogService
from yakoon.base.commands import Request
from yakoon.base.dispatch import CommandDispatch
from yakoon.base.flow.primitives import AwaitInput
from yakoon.base.runtime.input import InputEvent
from yakoon.platform.engine import CommandEngine
from yakoon.platform.host.scheduler import Scheduler
from yakoon.platform.runtime import Session


class Runner:
    scheduler: Scheduler
    engine: CommandEngine
    session: Session

    def __init__(self, session: Session, engine: CommandEngine, scheduler: Scheduler):
        self.session = session
        self.engine = engine
        self.scheduler = scheduler

        catalog = engine.services.get(CommandCatalogService)
        self._global_commands = {cmd.key for cmd in catalog.globals()}

    async def on_input(self, event: InputEvent):

        text = event.to_text()
        request = Request(text)

        # --------------------------------------------------
        # 0. System Command (immer Vorrang)
        # --------------------------------------------------
        if request.command in self._global_commands:
            await self.scheduler.dispatch(self.session, CommandDispatch(text))
            return

        flow = self.session.interaction_flow

        # --------------------------------------------------
        # 1. Flow vorhanden + AwaitInput
        # --------------------------------------------------
        if flow and isinstance(flow.control, AwaitInput):
            self.scheduler.resume_input(self.session, event)
            self.scheduler.schedule_flow(flow, self.session)
            return

        # --------------------------------------------------
        # 2. Flow vorhanden → Receive
        # --------------------------------------------------
        if flow:
            self.session.send_event(event)
            self.scheduler.schedule_flow(flow, self.session)
            return

        # --------------------------------------------------
        # 3. Kein Flow → Command Dispatch
        # --------------------------------------------------
        await self.scheduler.dispatch(self.session, CommandDispatch(text))
