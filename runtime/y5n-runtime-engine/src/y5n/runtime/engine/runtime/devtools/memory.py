import asyncio
import gc
from collections import Counter


class MemoryTrendMonitor:
    """Periodically logs the most frequent Python object types in memory.

    A lightweight diagnostic tool for development use. Runs in the background,
    prints trends in object allocation, and helps identify memory leaks or growth.
    """

    interval = 5
    _last = Counter()
    _running = False
    _task: asyncio.Task | None = None

    @classmethod
    def start(cls, interval: int = 5) -> None:
        """Starts the memory trend monitor.

        Args:
            interval: Logging interval in seconds. Defaults to 5.
        """
        cls.interval = interval
        if not cls._running:
            cls._running = True
            cls._task = asyncio.create_task(cls._run())

    @classmethod
    def stop(cls) -> None:
        """Stops the memory trend monitor."""
        cls._running = False
        if cls._task:
            cls._task.cancel()
            cls._task = None

    @classmethod
    async def _run(cls) -> None:
        """Background task that logs memory snapshots at the specified interval."""
        while cls._running:
            await asyncio.sleep(cls.interval)
            cls._log_snapshot()

    @classmethod
    def _log_snapshot(cls) -> None:
        """Logs the current top object types and their trends."""
        gc.collect()
        now = Counter(type(obj).__name__ for obj in gc.get_objects())
        output = []

        for typename in sorted(now, key=now.get, reverse=True)[:8]:
            prev = cls._last.get(typename, 0)
            curr = now[typename]
            diff = curr - prev
            trend = "⬆️" if curr > prev else "⬇️" if curr < prev else "→"
            output.append(f"{typename:20} {curr:5} ({diff}) {trend}")

        cls._last = now
        print("\n[Memory] Top object types:")
        print("\n".join(output))
