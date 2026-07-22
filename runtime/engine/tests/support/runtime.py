from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.primitives import Outcome, Stop
from y5n.runtime.engine.flow import Flow

from support.events import push_event
from support.flow import make_flow

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from y5n.runtime.engine.machine.engine import CommandEngine
    from y5n.runtime.engine.machine.scheduler import Scheduler
    from y5n.runtime.engine.runtime.sessions.session import Session

    _Handler = Callable[..., AsyncGenerator[Outcome | None, Any]]


class RuntimeHarness:

    def __init__(
        self,
        session: Session,
        scheduler: Scheduler,
        engine: CommandEngine,
    ) -> None:
        self.session = session
        self.scheduler = scheduler
        self.engine = engine

    async def start(
        self,
        handler: _Handler,
        *,
        payload: object = "test",
    ) -> Flow:
        flow = make_flow(handler, session=self.session, payload=payload)  # type: ignore[arg-type]
        self.scheduler.schedule_flow(flow, self.session)
        return flow

    async def run_until_blocked(self, flow: Flow) -> Outcome:
        while True:
            outcome = await self.engine.step_flow(flow, self.session)
            if outcome is None:
                continue
            await self.scheduler._handle_outcome(self.session, flow, outcome)
            return outcome

    async def run_until_stop(self, flow: Flow) -> Outcome:
        while True:
            outcome = await self.run_until_blocked(flow)
            if isinstance(outcome.control, Stop):
                return outcome

    def send_user_input(self, flow: Flow, text: str) -> None:
        push_event(self.session, Scope.USER_INPUT, "__user__", text, flow=flow)

    def send_flow(self, flow: Flow, channel: str, payload: object) -> None:
        push_event(self.session, Scope.FLOW, channel, payload, flow=flow)

    def send_session(self, channel: str, payload: object) -> None:
        push_event(self.session, Scope.SESSION, channel, payload)
