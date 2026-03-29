import asyncio
import heapq
import time
from collections import deque

from yakoon.base.capabilities.audit import AuditLogService
from yakoon.base.dispatch import DispatchInput
from yakoon.base.flow.primitives import Control
from yakoon.base.presentation import (
    OutputStream,
    v_error_domain,
    v_error_fatal,
    v_error_system,
)
from yakoon.base.runtime.input import InputEvent
from yakoon.platform.engine import CommandEngine
from yakoon.platform.flow import Flow, FlowKind
from yakoon.platform.runtime import DomainError, PlatformError
from yakoon.platform.runtime.sessions import Session


class Scheduler:

    # PULSE
    # --------------------------------------------------------
    MAX_STEPS_PER_CYCLE = 20  # konservativ
    MAX_TIME_PER_CYCLE = 0.01  # 10 ms
    MAX_ITERATIONS = 1000

    MAX_STEPS_PER_FLOW = 10
    MAX_TIME_PER_FLOW = 0.002
    # --------------------------------------------------------

    def __init__(self, engine: CommandEngine):
        self.engine = engine
        self.output = engine.services.get(OutputStream)

        # Flow-basierte Queue: (session, flow)
        self.ready_user = deque()
        self.ready_system = deque()

        self.sleeping = []  # (wake_at, session, flow)
        self._event = asyncio.Event()
        self._running = False

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    async def dispatch(self, session: Session, dispatch_input: DispatchInput):
        try:
            await self.engine.dispatch(session, dispatch_input)

            # alle Flows der Session schedulen
            for flow in session.flows():
                self.schedule_flow(flow, session)

        except PlatformError as e:
            await self.output.send_view(
                session, v_error_system(e.message, error_code=e.code)
            )

        except Exception as e:
            self.engine.services.get(AuditLogService).error(e, session)
            await self.output.send_view(
                session, v_error_system("Fatal error", error_kind="fatal")
            )

    def resume_input(self, session: Session, event: InputEvent):

        flow = session.interaction_flow
        if not flow:
            return

        # Queue statt single input
        flow.input_queue.append((flow.input_version, event))

        # Flow wieder schedulen (nicht Session!)
        self.schedule_flow(flow, session)

    def schedule_sleep(self, flow, session, wake_at):
        flow.wake_at = wake_at
        heapq.heappush(self.sleeping, (wake_at, session, flow))

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    async def run(self):
        self._running = True

        while self._running:

            steps = 0
            iterations = 0

            self._wake_sleeping()

            # --------------------------------------------------
            # Nichts zu tun → warten
            # --------------------------------------------------
            if not self.ready_user and not self.ready_system:
                if self.sleeping:
                    wake_at = self.sleeping[0][0]
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
                self.ready_user or self.ready_system
            ) and steps < self.MAX_STEPS_PER_CYCLE:

                if time.time() - start > self.MAX_TIME_PER_CYCLE:
                    break

                # ----------------------------------------------
                # Flow holen (System priorisiert)
                # ----------------------------------------------
                if self.ready_system:
                    session, flow = self.ready_system.popleft()
                elif self.ready_user:
                    session, flow = self.ready_user.popleft()
                else:
                    break

                flow.scheduled = False

                iterations += 1
                if iterations > self.MAX_ITERATIONS:
                    self.engine.services.get(AuditLogService).warning(
                        "Scheduler iteration limit reached", session
                    )
                    break

                control = flow.control

                # ----------------------------------------------
                # BLOCKED: AwaitInput
                # ----------------------------------------------
                if control and not control.is_runnable(flow):
                    continue

                # ----------------------------------------------
                # EXECUTE (mit per-flow Budget)
                # ----------------------------------------------
                flow_steps = 0
                flow_start = time.time()

                try:

                    while True:
                        outcome = await self.engine.step_flow(flow, session)

                        flow_steps += 1
                        steps += 1

                        # ----------------------------------
                        # Outcome behandeln
                        # ----------------------------------
                        if outcome:
                            await self._handle_outcome(session, flow, outcome)
                            break  # Flow ist fertig / blockiert

                        # ----------------------------------
                        # Budget prüfen (Flow)
                        # ----------------------------------
                        if flow_steps >= self.MAX_STEPS_PER_FLOW:
                            self.schedule_flow(flow, session)
                            break

                        if time.time() - flow_start > self.MAX_TIME_PER_FLOW:
                            self.schedule_flow(flow, session)
                            break

                except DomainError as e:
                    if session.interaction_flow:
                        session.del_flow(session.interaction_flow)
                    await self.output.send_view(
                        session, v_error_domain(e.message, error_code=e.code)
                    )

                except PlatformError as e:
                    await self.output.send_view(
                        session, v_error_system(e.message, error_code=e.code)
                    )

                except Exception as e:
                    self.engine.services.get(AuditLogService).error(e, session)
                    await self.output.send_view(
                        session, v_error_fatal("Fatal error", title="Fatal")
                    )

            # --------------------------------------------------
            # Yield zurück an Event Loop
            # --------------------------------------------------
            if (
                steps >= self.MAX_STEPS_PER_CYCLE
                or time.time() - start > self.MAX_TIME_PER_CYCLE
            ):
                await asyncio.sleep(0)

    def schedule_flow(self, flow, session):

        if flow.scheduled:
            return

        flow.scheduled = True

        if flow.kind == FlowKind.SYSTEM:
            self.ready_system.append((session, flow))
        else:
            self.ready_user.append((session, flow))

        self._event.set()

    # --------------------------------------------------------
    # INTERNAL
    # --------------------------------------------------------

    def _wake_sleeping(self):
        now = time.time()

        while self.sleeping and self.sleeping[0][0] <= now:
            _, session, flow = heapq.heappop(self.sleeping)

            control = flow.control
            if not control:
                continue

            control.on_wake(flow, self, session)

    async def _handle_outcome(self, session: Session, flow: Flow, outcome):

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
            control.on_enter(flow, self, session)
            return

        raise RuntimeError(f"Unhandled control: {type(control)}")
