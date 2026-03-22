import asyncio
import heapq
import time
from collections import deque

from yakoon.base.capabilities.audit.port import AuditLogService
from yakoon.base.engine.types import DispatchInput
from yakoon.base.runtime.commands import (
    AwaitInput,
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

    def __init__(self, engine: CommandEngine):
        self.engine = engine

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
            self._schedule(session)
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

        # if flow.state == FlowState.WAITING_INPUT:
        #    flow.state = FlowState.READY
        self._schedule(session)

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    async def run(self):
        self._running = True

        while self._running:

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

            # --------------------------------------------------
            # Work vorhanden
            # --------------------------------------------------
            session: Session = self.ready.popleft()

            # Multi-Flow: nur prüfen, ob überhaupt Flows existieren
            if not session.flows():
                continue

            try:
                results = await self.engine.tick(session)

                for flow, outcome in results:
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

    # --------------------------------------------------------
    # INTERNAL
    # --------------------------------------------------------

    def _schedule(self, session):
        if session not in self.ready:
            self.ready.append(session)
        self._event.set()

    def _wake_sleeping(self):
        now = time.time()

        while self.sleeping and self.sleeping[0][0] <= now:
            _, session, flow = heapq.heappop(self.sleeping)

            if flow.state != FlowState.SLEEPING:
                continue

            flow.state = FlowState.READY
            self._schedule(session)

    async def _handle_outcome(self, session: Session, flow: Flow, outcome):

        match outcome:

            case Next():
                flow.state = FlowState.READY
                self._schedule(session)

            case Stop():
                session.del_flow(flow)

            case AwaitInput() as a:
                # neue Version starten
                flow.state = FlowState.WAITING_INPUT
                flow.input_version += 1
                if a.emit:
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
