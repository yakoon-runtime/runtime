from __future__ import annotations


class _SessionList:
    def __await__(self):
        from y5n.runtime.api.runtime.bus import get_bus
        from y5n.runtime.api.runtime.invoke import Call

        bus = get_bus()
        resp = yield from bus.async_dispatch(
            Call(
                port="source",
                method="read",
                args={"query": "system:sessions --list"},
                caller_path="",
            )
        ).__await__()
        data = resp.result if hasattr(resp, "result") else resp
        rows = data.rows if hasattr(data, "rows") else []
        return rows


class _SessionAttach:
    __slots__ = ("_target_key",)

    def __init__(self, target_key: str) -> None:
        self._target_key = target_key

    def __await__(self):
        from y5n.runtime.api.runtime.bus import get_bus
        from y5n.runtime.api.runtime.invoke import Call
        from y5n.sdk.context import session as ctx_session

        bus = get_bus()
        yield from bus.async_dispatch(
            Call(
                port="session",
                method="attach",
                args={
                    "session_key": ctx_session().key,
                    "target_key": self._target_key,
                },
                caller_path="",
            )
        ).__await__()


class _SessionDetach:
    def __await__(self):
        from y5n.runtime.api.runtime.bus import get_bus
        from y5n.runtime.api.runtime.invoke import Call
        from y5n.sdk.context import session as ctx_session

        bus = get_bus()
        yield from bus.async_dispatch(
            Call(
                port="session",
                method="detach",
                args={"session_key": ctx_session().key},
                caller_path="",
            )
        ).__await__()


class _SessionCurrent:
    def __await__(self):
        from y5n.runtime.api.runtime.bus import get_bus
        from y5n.runtime.api.runtime.invoke import Call
        from y5n.runtime.api.runtime.context import current_context
        from y5n.sdk.libs.models import Session as _SessionModel

        ctx = current_context()
        session_key = ctx.get("session", {}).get("key", "")

        bus = get_bus()
        resp = yield from bus.async_dispatch(
            Call(
                port="session",
                method="current",
                caller_path="",
                caller_session_key=session_key,
            )
        ).__await__()
        data = resp.result if hasattr(resp, "result") else resp
        return _SessionModel.from_context(
            {"key": data.get("key"), "lang": data.get("lang"), "data": data.get("data", {})},
            {"id": data.get("user_id"), "name": data.get("user_name")},
        )


class _Session:
    def list(self) -> _SessionList:
        return _SessionList()

    def attach(self, target_key: str) -> _SessionAttach:
        return _SessionAttach(target_key)

    def detach(self) -> _SessionDetach:
        return _SessionDetach()

    def current(self) -> _SessionCurrent:
        return _SessionCurrent()


session = _Session()


__all__ = ["session"]
