from __future__ import annotations

from y5n.runtime.api.host.protocol import Marker, MarkerKind


class _NetworkList:
    def __await__(self):
        from y5n.runtime.api.runtime.bus import get_bus
        from y5n.runtime.api.runtime.context import Call

        bus = get_bus()
        resp = yield from bus.async_dispatch(
            Call(
                port="source",
                method="read",
                args={"query": "system:runtimes --list"},
                caller_path="",
            )
        ).__await__()
        data = resp.result if hasattr(resp, "result") else resp
        rows = data.rows if hasattr(data, "rows") else []
        return [{"name": r["name"], "url": r["url"]} for r in rows]


class _NetworkResolve:
    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        self._name = name

    def __await__(self):
        from y5n.runtime.api.runtime.bus import get_bus
        from y5n.runtime.api.runtime.context import Call

        bus = get_bus()
        resp = yield from bus.async_dispatch(
            Call(
                port="source",
                method="read",
                args={"query": f"system:runtimes --resolve {self._name}"},
                caller_path="",
            )
        ).__await__()
        data = resp.result if hasattr(resp, "result") else resp
        rows = data.rows if hasattr(data, "rows") else []
        return rows[0]["url"] if rows else None


class _Network:
    def list(self) -> _NetworkList:
        return _NetworkList()

    def resolve(self, name: str) -> _NetworkResolve:
        return _NetworkResolve(name)


network = _Network()


__all__ = ["network"]
