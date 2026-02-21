import asyncio
import threading
from collections.abc import Coroutine
from concurrent.futures import Future
from typing import Any

from yakoon.base.models.input import CommandDispatch


class SessionRunner:

    def __init__(self, engine):
        self.engine = engine
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._queue: asyncio.Queue[str] | None = None

    def submit_coro(self, coro: Coroutine[Any, Any, Any]) -> Future:
        if not self._loop:
            raise RuntimeError("Runner loop not started")
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def start(self):
        if self._thread:
            return

        self._thread = threading.Thread(target=self._thread_main, daemon=True)
        self._thread.start()

    def _thread_main(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._queue = asyncio.Queue()
        self._loop.create_task(self._run())
        self._loop.run_forever()

    def enqueue(self, session, text: str):
        # thread-safe: enqueue in runner loop
        if not self._loop or not self._queue:
            return
        self._loop.call_soon_threadsafe(self._queue.put_nowait, (session, text))

    async def _run(self):
        assert self._queue is not None
        while True:
            session, text = await self._queue.get()
            await self.engine.dispatch(session, CommandDispatch(text=text))

            if hasattr(session, "has_signal") and session.has_signal("exit_app"):
                break
