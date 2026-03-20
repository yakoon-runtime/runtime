import asyncio
import heapq
import time
from collections import deque

from yakoon.base.runtime.commands import (
    AwaitInput,
    Next,
    Sleep,
    SleepUntil,
    Stop,
)
from yakoon.platform.engine import CommandEngine


class Scheduler:

    def __init__(self, engine: CommandEngine):
        self.engine = engine

        self.ready = deque()  # flows ready to run
        self.sleeping = []  # (wake_at, session)
        self.waiting_input = {}  # session_id -> session
        self.ready_set = set()
        self._running = False

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def schedule(self, session):
        """Put a session into ready queue."""
        sid = id(session)

        if sid in self.ready_set:
            return

        self.ready.append(session)
        self.ready_set.add(sid)

    def resume_input(self, session, data):
        """Resume a flow with user input."""

        if not session.flow:
            return

        # Input immer puffern
        session.flow.input_queue.append(data)

        # NUR wenn Flow wirklich wartet:
        if id(session) in self.waiting_input:
            self.waiting_input.pop(id(session), None)
            self.schedule(session)

    # --------------------------------------------------------
    # Main loop
    # --------------------------------------------------------

    async def run(self):
        self._running = True

        while self._running:

            # 1. Wake sleeping flows
            self._wake_sleeping()

            # 2. Nothing to do → sleep until next event
            if not self.ready:
                await self._idle_wait()
                continue

            # 3. Run one step
            session = self.ready.popleft()
            self.ready_set.discard(id(session))
            if session.flow and session.flow.sleeping:
                continue

            outcome = await self.engine.tick(session)

            await self._handle_outcome(session, outcome)

    # --------------------------------------------------------
    # Internal
    # --------------------------------------------------------

    def _wake_sleeping(self):
        now = time.time()

        while self.sleeping and self.sleeping[0][0] <= now:
            _, session = heapq.heappop(self.sleeping)
            session.flow.sleeping = False
            self.ready.append(session)

    async def _idle_wait(self):
        if self.sleeping:
            wake_at = self.sleeping[0][0]
            delay = max(0, wake_at - time.time())
            await asyncio.sleep(delay)
        else:
            # nothing at all → small sleep
            await asyncio.sleep(0.05)

    async def _handle_outcome(self, session, outcome):

        # ----------------------------------------
        # CONTINUE
        # ----------------------------------------
        if outcome is None:
            # optional fallback
            return

        match outcome:

            # ----------------------------
            # RUNNING
            # ----------------------------
            case Next():
                self.ready.append(session)

            # ----------------------------
            # FINISHED
            # ----------------------------
            case Stop():
                session.flow = None

            # ----------------------------
            # INPUT
            # ----------------------------
            case AwaitInput() as ask:
                self.waiting_input[id(session)] = session

                view = ask.block
                await session.interaction.show_view(view)

            # ----------------------------
            # SLEEP
            # ----------------------------
            case Sleep(seconds=s):
                if session.flow.sleeping:
                    return
                wake_at = time.time() + s
                heapq.heappush(self.sleeping, (wake_at, session))
                session.flow.sleeping = True

            case SleepUntil(timestamp=t):
                if session.flow.sleeping:
                    return
                heapq.heappush(self.sleeping, (t, session))
                session.flow.sleeping = True

            # ----------------------------
            # SAFETY
            # ----------------------------
            case _:
                raise RuntimeError(f"Unhandled outcome: {type(outcome)}")
