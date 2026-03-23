import asyncio
import heapq
import time
from collections import deque

from yakoon.base.capabilities.audit.port import AuditLogService
from yakoon.base.engine.types import DispatchInput
from yakoon.base.runtime.commands import (
    AwaitInput,
    InputResolved,
    Next,
    Sleep,
    SleepUntil,
    Stop,
)
from yakoon.base.runtime.sessions.flow import Flow, FlowState
from yakoon.base.runtime.sessions.session import Session
from yakoon.base.ui import v_error_domain, v_error_fatal, v_error_system
from yakoon.platform.engine import CommandEngine
from yakoon.platform.runtime import PlatformError
from yakoon.platform.runtime.error import DomainError


class Scheduler:

    # PULSE
    # --------------------------------------------------------
    MAX_STEPS_PER_CYCLE = 20  # konservativ
    MAX_TIME_PER_CYCLE = 0.01  # 10 ms
    MAX_ITERATIONS = 1000
    # --------------------------------------------------------

    def __init__(self, engine: CommandEngine):
        self.engine = engine

        # Flow-basierte Queue: (session, flow)
        self.ready = deque()

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
            await session.emit(v_error_system(e.message, error_kind=e.code))  # type: ignore
        except Exception as e:
            self.engine.services.get(AuditLogService).error(e, session)
            await session.emit(v_error_system("Fatal error", error_kind="fatal"))

    def resume_input(self, session: Session, data):

        flow = session.focused_flow
        if not flow:
            return

        # Queue statt single input
        flow.input_queue.append((flow.input_version, data))

        # Flow wieder schedulen (nicht Session!)
        self.schedule_flow(flow, session)

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    async def run(self):
        self._running = True

        while self._running:

            steps = 0  # Quota-Counter pro Zyklus
            iterations = 0
            self._wake_sleeping()

            # --------------------------------------------------
            # Nichts zu tun → warten
            # --------------------------------------------------
            if not self.ready:
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
            while self.ready and steps < self.MAX_STEPS_PER_CYCLE:

                if time.time() - start > self.MAX_TIME_PER_CYCLE:
                    break

                # --------------------------------------------------
                # Work vorhanden
                # --------------------------------------------------
                session, flow = self.ready.popleft()

                iterations += 1
                if iterations > self.MAX_ITERATIONS:
                    self.engine.services.get(AuditLogService).warning(
                        "Scheduler iteration limit reached", session
                    )
                    break

                if flow.state == FlowState.READY:
                    pass  # normal

                # WAITING_INPUT = passiv
                elif flow.state == FlowState.WAITING_INPUT:
                    if not flow.input_queue:
                        continue

                elif flow.state == FlowState.SLEEPING:
                    if flow.wake_at is not None:
                        heapq.heappush(self.sleeping, (flow.wake_at, session, flow))
                    continue

                else:
                    # unbekannter Zustand → loggen
                    self.engine.services.get(AuditLogService).warning(
                        f"Flow in unexpected state: {flow.state}", session
                    )
                    continue

                try:
                    # EIN Flow pro Tick
                    outcome = await self.engine.tick_flow(flow, session)

                    steps += 1

                    if outcome:
                        await self._handle_outcome(session, flow, outcome)

                except DomainError as e:
                    if session.focused_flow:
                        session.del_flow(session.focused_flow)
                    await session.emit(v_error_domain(e.message, error_code=e.code))  # type: ignore

                except PlatformError as e:
                    await session.emit(v_error_system(e.message, error_kind=e.code))  # type: ignore

                except Exception as e:
                    self.engine.services.get(AuditLogService).error(e, session)
                    await session.emit(v_error_fatal("Fatal error", title="Fatal"))

            # WICHTIG: Kontrolle zurück an EventLoop
            if (
                steps >= self.MAX_STEPS_PER_CYCLE
                or time.time() - start > self.MAX_TIME_PER_CYCLE
            ):
                await asyncio.sleep(0)

    def schedule_flow(self, flow: Flow, session: Session):
        # bewusst KEIN dedupe -> echtes Round-Robin
        self.ready.append((session, flow))
        self._event.set()

    # --------------------------------------------------------
    # INTERNAL
    # --------------------------------------------------------

    def _wake_sleeping(self):
        now = time.time()

        while self.sleeping and self.sleeping[0][0] <= now:
            _, session, flow = heapq.heappop(self.sleeping)

            if flow.state != FlowState.SLEEPING:
                continue

            flow.state = FlowState.READY

            #  Flow wieder einreihen
            self.schedule_flow(flow, session)

    async def _handle_outcome(self, session: Session, flow: Flow, outcome):

        match outcome:

            case Next():
                # Round-Robin: hinten anstellen
                flow.state = FlowState.READY
                self.schedule_flow(flow, session)

            case Stop():
                session.del_flow(flow)

            case InputResolved() as ir:
                # einfach weiterlaufen lassen
                flow.state = FlowState.READY
                self.schedule_flow(flow, session)

            case AwaitInput() as a:
                # neue Version starten
                flow.state = FlowState.WAITING_INPUT
                flow.input_version += 1
                if a.emit and a.view:
                    await session.emit(a.view)

            case Sleep(seconds=s):
                flow.state = FlowState.SLEEPING
                wake_at = time.time() + s
                heapq.heappush(self.sleeping, (wake_at, session, flow))

            case SleepUntil(timestamp=t):
                flow.state = FlowState.SLEEPING
                heapq.heappush(self.sleeping, (t, session, flow))

            case _:
                raise RuntimeError(f"Unhandled outcome: {type(outcome)}")
