from __future__ import annotations

import asyncio
import threading
from typing import Any

from yakoon.base.host.ports import InputEvent
from yakoon.kivy.host import KivyHost
from yakoon.platform.host.runner import Runner


class TabRunnerThread:
    """Pro Tab ein eigener Runner-Thread (eigene asyncio-loop).

    Startet den platform Runner(engine, session, host). Input kommt über Host.deliver_text().
    """

    def __init__(
        self,
        *,
        engine: Any,
        session: Any,
        host: KivyHost,
        inits: list[str] | None = None,
    ):
        self.engine = engine
        self.session = session
        self.host = host
        self.inits = inits or []

        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._runner: Runner | None = None

    @property
    def loop(self) -> asyncio.AbstractEventLoop | None:
        return self._loop

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
        self._loop.create_task(self._run())
        self._loop.run_forever()

    async def _run(self) -> None:
        async def submit(event: InputEvent) -> None:
            runner = self._runner
            if runner is None:
                return
            if isinstance(event, InputEvent):
                await runner.on_input_submit(event.data)
            elif isinstance(event, InputEvent):
                await runner.on_user_input(event.value)
            else:
                raise TypeError(f"Unsupported event: {type(event)}")

        # Host ist bereits im UI-Thread gebaut; wir injizieren hier nur submit
        # (Host selber ist thread-safe via deliver_text()).
        self.host._submit = submit  # type: ignore[attr-defined]

        self._runner = Runner(
            engine=self.engine, session=self.session, interaction=self.host
        )
        await self._runner.start(self.inits)

        loop = asyncio.get_running_loop()
        loop.call_soon(loop.stop)
