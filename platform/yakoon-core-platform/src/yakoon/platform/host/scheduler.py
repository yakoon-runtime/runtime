import asyncio
import heapq
import time
from collections import deque

from yakoon.base.engine.flow import FlowState
from yakoon.base.runtime.commands.steps.outcome import AwaitInput, Sleep, SleepUntil
from yakoon.platform.engine.engine import CommandEngine


class Scheduler:

    def __init__(self, engine: CommandEngine):
        self.engine = engine

        self.ready = deque()  # flows ready to run
        self.sleeping = []  # (wake_at, session)
        self.waiting_input = {}  # session_id -> session

        self._running = False

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def schedule(self, session):
        """Put a session into ready queue."""
        self.ready.append(session)

    def resume_input(self, session, data):
        """Resume a flow with user input."""
        session.flow["input"] = data
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
            result = await self.engine.tick(session)

            await self._handle_result(session, result)

    # --------------------------------------------------------
    # Internal
    # --------------------------------------------------------

    def _wake_sleeping(self):
        now = time.time()

        while self.sleeping and self.sleeping[0][0] <= now:
            _, session = heapq.heappop(self.sleeping)
            self.ready.append(session)

    async def _idle_wait(self):
        if self.sleeping:
            wake_at = self.sleeping[0][0]
            delay = max(0, wake_at - time.time())
            await asyncio.sleep(delay)
        else:
            # nothing at all → small sleep
            await asyncio.sleep(0.05)

    async def _handle_result(self, session, result):

        if result.state == FlowState.RUNNING:
            self.ready.append(session)
            return

        if result.state == FlowState.FINISHED:
            session.flow = None
            return

        if result.state == FlowState.WAITING:

            outcome = result.outcome

            # ----------------------------------------
            # INPUT
            # ----------------------------------------
            if isinstance(outcome, AwaitInput):
                self.waiting_input[id(session)] = session

                # UI trigger
                view = outcome.block
                await session.interaction.prompt(view=view)
                return

            # ----------------------------------------
            # SLEEP
            # ----------------------------------------
            if isinstance(outcome, Sleep):
                wake_at = time.time() + outcome.seconds
                heapq.heappush(self.sleeping, (wake_at, session))
                return

            if isinstance(outcome, SleepUntil):
                heapq.heappush(self.sleeping, (outcome.timestamp, session))
                return
