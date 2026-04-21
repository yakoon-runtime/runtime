from __future__ import annotations

from yakoon.base.runtime import InputEvent
from yakoon.platform.runtime import Session

from .engine import CommandEngine
from .scheduler import Scheduler


class Runner:

    def __init__(
        self,
        session: Session,
        engine: CommandEngine,
        scheduler: Scheduler,
        global_commands: set,
    ):
        self._session = session
        self._engine = engine
        self._scheduler = scheduler
        self._global_commands = global_commands

    async def on_input(self, event: InputEvent):

        if event.command in self._global_commands:
            await self._scheduler.dispatch(self._session, event)
            return

        flow = self._session.interaction_flow
        if flow:
            flow.push_event(event)
            self._scheduler.schedule_flow(flow, self._session)
            return

        await self._scheduler.dispatch(self._session, event)


class RunnerFactory:

    def __init__(
        self,
        engine: CommandEngine,
        scheduler: Scheduler,
        global_commands: set,
    ):
        self._engine = engine
        self._scheduler = scheduler
        self._global_commands = global_commands

    def create(self, session):
        return Runner(session, self._engine, self._scheduler, self._global_commands)
