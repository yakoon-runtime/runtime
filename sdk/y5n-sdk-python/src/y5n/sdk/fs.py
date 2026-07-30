from __future__ import annotations

from y5n.runtime.api.flow.primitives import CwdEffect, Outcome


class _Chdir:
    __slots__ = ("_path",)

    def __init__(self, path: str) -> None:
        self._path = path

    def __await__(self):
        yield Outcome(effects=[CwdEffect(self._path)])


class _FS:
    def chdir(self, path: str) -> _Chdir:
        return _Chdir(path)


fs = _FS()


__all__ = ["fs"]
