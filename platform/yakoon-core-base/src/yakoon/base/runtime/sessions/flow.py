import asyncio


class FlowControl:

    def __init__(self):

        self._pending = 0
        self._ready = asyncio.Event()
        self._ready.set()

    def acquire(self) -> None:

        self._pending += 1

        if self._pending == 1:
            self._ready.clear()
            # print("acquire")

    def try_acquire(self) -> bool:

        if self._pending == 0:
            self.acquire()
            return True

        return False

    def release(self) -> None:

        if self._pending == 0:
            return

        self._pending -= 1

        if self._pending == 0:
            self._ready.set()
            # print("Release")

    async def wait_ready(self) -> None:

        await self._ready.wait()

    def is_ready(self) -> bool:

        return self._pending == 0
