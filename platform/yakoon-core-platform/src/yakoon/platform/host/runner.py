from __future__ import annotations

from yakoon.base.catalogs.port import CommandCatalogService
from yakoon.base.commands import Request
from yakoon.base.dispatch import CommandDispatch
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
        if request.command in self._global_commands:
            await self.scheduler.dispatch(self.session, CommandDispatch(text))
            return

        flow = self.session.interaction_flow
        if flow:
            flow.push_event(event)
            self.scheduler.schedule_flow(flow, self.session)
            return

        await self.scheduler.dispatch(self.session, CommandDispatch(text))
