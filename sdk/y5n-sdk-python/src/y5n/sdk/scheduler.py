from __future__ import annotations

from y5n.runtime.api.flow.primitives import (
    Background,
    FlowBgEffect,
    FlowFgEffect,
    FlowListEffect,
    FlowStopEffect,
    Outcome,
    Suspend,
)


class _FlowsList:
    def __await__(self):
        from y5n.sdk.context import flow as _ctx_flow

        exclude_id = _ctx_flow().id
        result = yield Outcome(effects=[FlowListEffect(exclude_id=exclude_id)])
        return result


class _Suspend:
    def __await__(self):
        event = yield Outcome(control=Suspend(), effects=[Background()])
        return event


class _FlowStop:
    __slots__ = ("_flow_id",)

    def __init__(self, flow_id: str) -> None:
        self._flow_id = flow_id

    def __await__(self):
        yield Outcome(effects=[FlowStopEffect(flow_id=self._flow_id)])


class _FlowFg:
    __slots__ = ("_flow_id",)

    def __init__(self, flow_id: str | None = None) -> None:
        self._flow_id = flow_id

    def __await__(self):
        flow_id = self._flow_id
        if flow_id is None:
            from y5n.sdk.context import flow as _ctx_flow

            flow_id = _ctx_flow().id
        yield Outcome(effects=[FlowFgEffect(flow_id=flow_id)])


class _FlowBg:
    def __await__(self):
        result = yield Outcome(effects=[FlowBgEffect()])
        return result


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
