from __future__ import annotations

from yakoon.base.catalogs.port import CommandRegistry
from yakoon.base.commands import Request
from yakoon.base.runtime import InputEvent
from yakoon.platform.machine import CommandEngine
from yakoon.platform.machine.scheduler import Scheduler
from yakoon.platform.runtime import Session


class Runner:
    scheduler: Scheduler
    engine: CommandEngine
    session: Session

    def __init__(self, session: Session, engine: CommandEngine, scheduler: Scheduler):
        self.session = session
        self.engine = engine
        self.scheduler = scheduler

        catalog = engine.container.get(CommandRegistry)
        self._global_commands = {cmd.key for cmd in catalog.globals()}

    async def on_input(self, event: InputEvent):

        text = event.to_text()

        request = Request(text)
        if request.command in self._global_commands:
            await self.scheduler.dispatch(self.session, event)
            return

        flow = self.session.interaction_flow
        if flow:
            flow.push_event(event)
            self.scheduler.schedule_flow(flow, self.session)
            return

        await self.scheduler.dispatch(self.session, event)
