from __future__ import annotations

import asyncio
import heapq
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Protocol
from uuid import uuid4

from y5n.base.flow.channel import Scope
from y5n.base.flow.primitives import (
    AwaitEvent,
    Control,
    Outcome,
    Stop,
    YieldToScheduler,
)
from y5n.base.nodes import Node
from y5n.base.projection import Projection
from y5n.base.runtime import Event, InputContext
from y5n.runtime.flow import Flow, FlowKind
from y5n.runtime.runtime import Session


class Scheduler:
    """Cooperative async scheduler for flows.

    Maintains ready queues (user/system), a sleep heap for delayed flows,
    and per-flow step budgets.  The main loop wakes sleeping flows,
    dispatches ready flows to the engine, and handles outcomes.
    """

    # PULSE
    # --------------------------------------------------------
    MAX_STEPS_PER_CYCLE = 20  # konservativ
    MAX_TIME_PER_CYCLE = 0.01  # 10 ms
    MAX_ITERATIONS = 1000

    MAX_STEPS_PER_FLOW = 10
    MAX_TIME_PER_FLOW = 0.002
    # --------------------------------------------------------

    def __init__(
        self,
        platform: Node,
        on_setup: OnSetup,
        on_dispatch: OnDispatch,
        on_step_flow: OnStepFlow,
        on_show_projection: OnShowProjection,
        on_audit_warning: OnAuditWarning,
        on_error_resolve: OnErrorResolve,
    ):
        self.platform = platform

        # Hooks
        self.on_setup = on_setup
        self.on_dispatch = on_dispatch
        self.on_step_flow = on_step_flow
        self.on_show_projection = on_show_projection
        self.on_audit_warning = on_audit_warning
        self.on_error_resolve = on_error_resolve

        # Flow-basierte Queue: (session, flow)
        self._ready_user = deque()
        self._ready_system = deque()

        self._sleeping = []  # (wake_at, session, flow)
        self._event = asyncio.Event()
        self._running = False

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    async def setup(self, session: Session, node: Node):
        await self._call_runtime(session, None, self.on_setup, node=node)

    async def dispatch(self, session: Session, event: Event):
        await self._call_runtime(session, event.context, self.on_dispatch, event=event)

    async def continue_flow(self, session, old_flow, event, pipeline):

        # 1. Dispatch (resolve + permission + create command)
        new_flow = await self.on_dispatch(session=session, event=event)
        assert new_flow, "runtime error"

        new_flow.pipeline = pipeline

        # 1. schedule new flow
        self.schedule_flow(new_flow, session)

        # 2. schedule old flow
        self.schedule_flow(old_flow, session)

    def schedule_sleep(self, flow, session, wake_at):
        flow.wake_at = wake_at
        heapq.heappush(self._sleeping, (wake_at, session, flow))

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    async def run(self):
        self._running = True

        while self._running:

            steps = 0
            iterations = 0

            await self._wake_sleeping()

            # --------------------------------------------------
            # Nothing to do → wait
            # --------------------------------------------------
            if not self._ready_user and not self._ready_system:
                if self._sleeping:
                    wake_at = self._sleeping[0][0]
                    delay = max(0, wake_at - time.time())

                    try:
                        await asyncio.wait_for(self._event.wait(), timeout=delay)
                    except TimeoutError:
                        pass
                else:
                    await self._event.wait()

                self._event.clear()
                continue

            start = time.time()

            # --------------------------------------------------
            # Main processing loop
            # --------------------------------------------------
            while (
                self._ready_user or self._ready_system
            ) and steps < self.MAX_STEPS_PER_CYCLE:

                if time.time() - start > self.MAX_TIME_PER_CYCLE:
                    break

                # ----------------------------------------------
                # Fetch next flow (system priority)
                # ----------------------------------------------
                session: Session
                if self._ready_system:
                    session, flow = self._ready_system.popleft()
                elif self._ready_user:
                    session, flow = self._ready_user.popleft()
                else:
                    break

                flow.scheduled = False

                iterations += 1
                if iterations > self.MAX_ITERATIONS:
                    self.on_audit_warning(
                        message="Scheduler iteration limit reached", session=session
                    )
                    break

                control = flow.control

                # ----------------------------------------------
                # BLOCKED: AwaitEvent
                # ----------------------------------------------
                if control and not control.is_runnable(flow, session):
                    continue

                # ----------------------------------------------
                # EXECUTE (with per-flow budget)
                # ----------------------------------------------
                flow_steps = 0
                flow_start = time.time()

                try:

                    while True:
                        outcome = await self.on_step_flow(flow=flow, session=session)

                        flow_steps += 1
                        steps += 1

                        # ----------------------------------
                        # Handle outcome
                        # ----------------------------------
                        if outcome:
                            await self._handle_outcome(session, flow, outcome)
                            self._refresh_resumed_flows(session)
                            break  # Flow done / blocked

                        # ----------------------------------
                        # Check budget (flow)
                        # ----------------------------------
                        if flow_steps >= self.MAX_STEPS_PER_FLOW:
                            self.schedule_flow(flow, session)
                            break

                        if time.time() - flow_start > self.MAX_TIME_PER_FLOW:
                            self.schedule_flow(flow, session)
                            break

                except Exception as error:
                    if session.foreground_flow:
                        session.del_flow(session.foreground_flow)
                    await self._show_error(session, None, flow.node, error)

            # --------------------------------------------------
            # Yield back to event loop
            # --------------------------------------------------
            if (
                steps >= self.MAX_STEPS_PER_CYCLE
                or time.time() - start > self.MAX_TIME_PER_CYCLE
            ):
                await asyncio.sleep(0)

    def schedule_flow(self, flow, session) -> None:

        if flow.scheduled:
            return

        flow.scheduled = True

        if flow.kind == FlowKind.SYSTEM:
            self._ready_system.append((session, flow))
        else:
            self._ready_user.append((session, flow))

        self._event.set()

    # --------------------------------------------------------
    # INTERNAL
    # --------------------------------------------------------

    def _refresh_resumed_flows(self, session):

        for flow in session.flows():

            if isinstance(flow.control, YieldToScheduler) and not flow.scheduled:
                self.schedule_flow(flow, session)

    async def _call_runtime(
        self,
        session: Session,
        ctx: InputContext | None,
        callback: Callable[..., Awaitable[Flow | None]],
        **kwargs,
    ):
        node: Node | None = None
        try:
            flow = await callback(session=session, **kwargs)
            if flow:
                node = flow.node

            # Schedule all flows of the session
            for flow in session.flows():
                self.schedule_flow(flow, session)

        except Exception as error:
            await self._show_error(session, ctx, node, error)

    async def _wake_sleeping(self):
        now = time.time()

        while self._sleeping and self._sleeping[0][0] <= now:
            _, session, flow = heapq.heappop(self._sleeping)

            control = flow.control
            if not control:
                continue

            await control.on_wake(flow, self, session)

    async def _handle_outcome(self, session: Session, flow: Flow, outcome: Outcome):

        control = outcome.control
        if control is None:
            return

        # ----------------------------------
        # 1. Single Source of Truth
        # ----------------------------------
        flow.control = control

        # ----------------------------------
        # 2. Verhalten
        # ----------------------------------

        if isinstance(control, Control):
            await control.on_enter(flow, self, session)

            # ----------------------------------
            # 3. Parent wecken (Projection liegt
            #    bereits im Channel)
            # ----------------------------------
            if isinstance(control, Stop) and flow.out_channel:
                session.push_event(
                    Scope.SESSION,
                    flow.out_channel,
                    Event(payload=None),
                )
                self._schedule_waiting(session, flow.out_channel)
            return

        raise RuntimeError(f"Unhandled control: {type(control)}")

    def _schedule_waiting(self, session: Session, channel: str):
        for f in session.flows():
            ctrl = f.control
            if isinstance(ctrl, AwaitEvent) and ctrl.channel == channel:
                self.schedule_flow(f, session)

    async def _show_error(self, session, ctx, node, error):

        try:
            projection = await self.on_error_resolve(
                node=node or self.platform,
                session=session,
                error=error,
            )

            await self.on_show_projection(
                session=session,
                projection=projection,
                ctx=ctx,
                job_id=uuid4().hex,
            )
        except Exception:
            logger = logging.getLogger("error")
            logger.critical(
                "Error while showing error projection for: %s",
                error,
                exc_info=True,
            )
            logger.critical(
                "Original error that triggered _show_error:",
                exc_info=(type(error), error, error.__traceback__),
            )


# ----------------------------------
# PORTS
# ----------------------------------


class OnDispatch(Protocol):
    async def __call__(self, *, session: Session, event: Event) -> Flow | None: ...


class OnSetup(Protocol):
    async def __call__(self, *, session: Session, node: Node) -> Flow | None: ...


class OnStepFlow(Protocol):
    async def __call__(self, *, flow: Flow, session: Session) -> Outcome | None: ...


class OnAuditWarning(Protocol):
    def __call__(self, *, message: str, session: Session) -> None: ...


class OnShowProjection(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        projection: Projection,
        ctx: InputContext | None,
        job_id: str = "system",
    ) -> None: ...


class OnErrorResolve(Protocol):
    async def __call__(
        self,
        *,
        node: Node,
        session: Session,
        error: Exception,
    ) -> Projection: ...
