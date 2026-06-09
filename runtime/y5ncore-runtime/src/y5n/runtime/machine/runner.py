from __future__ import annotations

from typing import Protocol

from y5n.base.flow.channel import Scope
from y5n.base.runtime import Event
from y5n.runtime.runtime import Session


class Runner:

    def __init__(
        self,
        session: Session,
        runtime_commands: set,
        on_dispatch: OnDispatch,
        on_schedule_flow: OnScheduleFlow,
    ):
        self._session = session
        self._runtime_commands = runtime_commands
        self.on_dispatch = on_dispatch
        self.on_schedule_flow = on_schedule_flow

    @property
    def session(self) -> Session:
        return self._session

    async def on_input(self, event: Event):

        if event.payload in self._runtime_commands:
            await self.on_dispatch(session=self._session, event=event)
            return

        flow = self._session.foreground_flow
        if flow:
            self._session.push_event(Scope.USER_INPUT, "__user__", event, flow=flow)
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
