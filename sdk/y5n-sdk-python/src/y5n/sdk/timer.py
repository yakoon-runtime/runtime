from __future__ import annotations

from y5n.runtime.api.host.protocol import Marker, MarkerKind


class _Delay:
    __slots__ = ("_seconds",)

    def __init__(self, seconds: float) -> None:
        self._seconds = seconds

    def __await__(self):
        yield Marker(MarkerKind.DELAY, self._seconds)


class _DelayUntil:
    __slots__ = ("_timestamp",)

    def __init__(self, timestamp: float) -> None:
        self._timestamp = timestamp

    def __await__(self):
        yield Marker(MarkerKind.DELAY_UNTIL, self._timestamp)


class _Timer:
    def delay(self, seconds: float) -> _Delay:
        return _Delay(seconds)

    def delay_until(self, timestamp: float) -> _DelayUntil:
        return _DelayUntil(timestamp)


timer = _Timer()


def delay(seconds: float) -> _Delay:
    return timer.delay(seconds)


def delay_until(timestamp: float) -> _DelayUntil:
    return timer.delay_until(timestamp)


__all__ = ["delay", "delay_until", "timer"]
