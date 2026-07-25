from __future__ import annotations

from typing import Any

from y5n.runtime.api.host.protocol import Marker, MarkerKind


class _View:
    __slots__ = ("_params",)

    def __init__(self, **params: Any) -> None:
        self._params = params

    def __await__(self):
        yield Marker(MarkerKind.VIEW, self._params)


class Viewport:
    def clear(self) -> _View:
        return _View(clear=True)

    def connect(self, url: str, name: str) -> _View:
        return _View(connect=url, connect_name=name)


viewport = Viewport()


__all__ = ["viewport"]
