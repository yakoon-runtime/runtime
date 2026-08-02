from __future__ import annotations

from typing import Any

from y5n.runtime.api.flow.primitives import (
    Background,
    FlowFgEffect,
    FlowStopEffect,
    Pulse,
    Suspend,
)

from .context import current as _current_context
from .libs import transport as _transport
from .libs.models import Call, Response


async def _invoke(call: Call) -> Response:
    result = await _transport.invoke(call.to_dict())
    if isinstance(result, dict):
        return Response.from_dict(result)
    return Response(result=result)


async def _do_call(call: Call):
    response = await _invoke(call)
    if response.error:
        raise RuntimeError(response.error)
    return response.result


def _call_runtime(method: str, **args: Any):
    ctx = _current_context()
    call = Call(
        port="runtime",
        method=method,
        args=args,
        caller_path=ctx.node.get("path", ""),
        caller_session_key=ctx.session.get("key", ""),
    )
    return _do_call(call)


class _FlowsList:
    def __await__(self):
        from y5n.sdk.context import flow as _ctx_flow

        exclude_id = _ctx_flow().id
        return _call_runtime("flows", exclude_id=exclude_id).__await__()


class _Suspend:
    def __await__(self):
        event = yield Pulse(control=Suspend(), effects=[Background()])
        return event


class _FlowStop:
    __slots__ = ("_flow_id",)

    def __init__(self, flow_id: str) -> None:
        self._flow_id = flow_id

    def __await__(self):
        yield Pulse(effects=[FlowStopEffect(flow_id=self._flow_id)])


class _FlowFg:
    __slots__ = ("_flow_id",)

    def __init__(self, flow_id: str | None = None) -> None:
        self._flow_id = flow_id

    def __await__(self):
        flow_id = self._flow_id
        if flow_id is None:
            from y5n.sdk.context import flow as _ctx_flow

            flow_id = _ctx_flow().id
        yield Pulse(effects=[FlowFgEffect(flow_id=flow_id)])


class _FlowBg:
    def __await__(self):
        return _call_runtime("background").__await__()


class _Scheduler:
    def flows(self) -> _FlowsList:
        return _FlowsList()

    def stop(self, flow_id: str) -> _FlowStop:
        return _FlowStop(flow_id)

    def foreground(self, flow_id: str | None = None) -> _FlowFg:
        return _FlowFg(flow_id)

    def background(self) -> _FlowBg:
        return _FlowBg()

    def suspend(self) -> _Suspend:
        return _Suspend()


scheduler = _Scheduler()


__all__ = ["scheduler"]
