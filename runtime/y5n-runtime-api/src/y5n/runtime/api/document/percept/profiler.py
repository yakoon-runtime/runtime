class StreamProfiler:

    def __init__(self):
        self.enabled = False

        self._start = 0.0
        self._events = 0
        self._chunks = 0
        self._chars = 0
        self._sleep = 0.0

    def reset(self):
        import time

        self._start = time.monotonic()
        self._events = 0
        self._chunks = 0
        self._chars = 0
        self._sleep = 0.0

    def event(self):
        if self.enabled:
            self._events += 1

    def chunk(self, n):
        if self.enabled:
            self._chunks += 1
            self._chars += n

    def sleep(self, t):
        if self.enabled:
            self._sleep += t

    def stats(self):

        import time

        if not self.enabled:
            return None

        now = time.monotonic()
        dt = max(now - self._start, 1e-6)

        return {
            "events/sec": self._events / dt,
            "chunks/sec": self._chunks / dt,
            "chars/sec": self._chars / dt,
            "sleep_ratio": self._sleep / dt,
        }
