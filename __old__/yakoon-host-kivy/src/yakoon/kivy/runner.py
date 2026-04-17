from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from concurrent.futures import Future
from typing import Any


class SessionRunner:
    """Kivy runtime runner.

    Dieser Runner macht nur noch zwei Dinge:
    1) Er stellt einen asyncio-Loop in einem Thread bereit (submit_coro), damit der UI-Thread
       async Services nutzen kann (z.B. SessionService.get_or_create).
    2) Pro Tab wird zusätzlich ein eigener TabRunnerThread gestartet, der den *platform Runner*
       ausführt (nicht mehr engine.dispatch).
    """

    def __init__(self, engine: Any):
        self.engine = engine
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    def submit_coro(self, coro: Coroutine[Any, Any, Any]) -> Future:
        if not self._loop:
            raise RuntimeError("Runner loop not started")
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def start(self) -> None:
        if self._thread:
            return
        self._thread = threading.Thread(target=self._thread_main, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _thread_main(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
