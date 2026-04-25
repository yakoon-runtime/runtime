from __future__ import annotations

from typing import Protocol

from yakoon.base.runtime import InputEvent
from yakoon.platform.runtime import Session


class Runner:

    def __init__(
        self,
        session: Session,
        global_commands: set,
        on_dispatch: OnDispatch,
        on_schedule_flow: OnScheduleFlow,
    ):
        self._session = session
        self._global_commands = global_commands
        self.on_dispatch = on_dispatch
        self.on_schedule_flow = on_schedule_flow

    async def on_input(self, event: InputEvent):

        if event.command in self._global_commands:
            await self.on_dispatch(session=self._session, event=event)
            return

        flow = self._session.interaction_flow
        if flow:
            flow.push_event(event)
            self.on_schedule_flow(flow=flow, session=self._session)
            return

        await self.on_dispatch(session=self._session, event=event)


# ----------------------------------
# PORTS
# ----------------------------------


class OnDispatch(Protocol):
    async def __call__(self, *, session, event) -> None: ...


class OnScheduleFlow(Protocol):
    def __call__(self, *, flow, session) -> None: ...


class OnCreateRunner(Protocol):
    def __call__(self, *, session) -> Runner: ...
