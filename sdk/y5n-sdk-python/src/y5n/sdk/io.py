from __future__ import annotations

import json
from typing import Any

from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.patterns.public import Form
from y5n.runtime.api.flow.primitives import (
    AwaitEvent,
    EmitEvent,
    EmitView,
    Foreground,
    Mode,
    Pulse,
)
from y5n.runtime.api.nodes import Param
from y5n.runtime.api.runtime import Event
from y5n.sdk.models import Document, Header, InlineText, Text, YdsModel
from y5n.sdk.models import Field as _FormFieldDef


def _resolve_view(view: str | dict) -> dict:
    if isinstance(view, dict):
        return view
    if view.startswith("{"):
        try:
            data = json.loads(view)
            if isinstance(data, dict) and data.get("kind") == "document":
                return data
        except Exception:
            pass
    return _text_document(view)


class _Write:
    __slots__ = ("_view", "_mode")
    _view: dict | str
    _mode: Mode | None

    def __init__(self, view: dict | str, mode: Mode | None = None) -> None:
        self._view = view
        self._mode = mode

    def __await__(self):
        yield Pulse(effects=[EmitView(_resolve_view(self._view), mode=self._mode)])


class _Error:
    __slots__ = ("_text",)

    def __init__(self, text: str) -> None:
        self._text = text

    def __await__(self):
        yield Pulse(
            effects=[EmitView({"kind": "error", "text": self._text}, mode=None)]
        )


class _Prompt:
    __slots__ = ("_projection",)

    def __init__(self, projection: dict | str) -> None:
        self._projection = projection

    def __await__(self):
        view = (
            self._projection
            if isinstance(self._projection, dict)
            else _text_document(self._projection)
        )
        result = yield Pulse(
            effects=[Foreground(), EmitView(view, persist=True)],
            control=AwaitEvent("__user__", scope=Scope.USER_INPUT),
        )
        return result


class _Receive:
    __slots__ = ("_channel", "_scope")
    _channel: str | None
    _scope: str | None

    def __init__(self, channel: str | None = None, scope: str | None = None) -> None:
        self._channel = channel
        self._scope = scope

    def __await__(self):
        channel = self._channel
        scope = Scope(self._scope) if isinstance(self._scope, str) else self._scope
        if scope is None:
            if channel is None:
                scope = Scope.USER_INPUT
                channel = "__user__"
            else:
                scope = Scope.FLOW
        elif channel is None:
            channel = "default"
        event = yield Pulse(control=AwaitEvent(channel, scope))
        return event


class _Form:
    __slots__ = ("_params",)

    def __init__(self, **params: Any) -> None:
        self._params = params

    def __await__(self):
        params = self._params
        fields = []
        for f in params.get("fields", []):
            if isinstance(f, dict):
                fields.append(
                    Param(
                        key=f.get("key", ""),
                        title=f.get("title", ""),
                        required=f.get("required", False),
                    )
                )
            else:
                fields.append(f)
        form = Form(
            fields=fields,
            title=params.get("title", ""),
            intro=params.get("intro", ""),
            initial=params.get("initial"),
            focus=params.get("focus"),
        )
        result = yield from form.pulse_flow()
        return result


class _Send:
    __slots__ = ("_channel", "_payload", "_scope")
    _channel: str
    _payload: Any
    _scope: str

    def __init__(self, channel: str, payload: Any = None, scope: str = "flow") -> None:
        self._channel = channel
        self._payload = payload
        self._scope = scope

    def __await__(self):
        scope = Scope(self._scope) if isinstance(self._scope, str) else self._scope
        yield Pulse(
            effects=[
                EmitEvent(self._channel, Event(payload=self._payload), scope=scope)
            ]
        )


class _IO:
    def write(
        self,
        view: YdsModel | dict | str,
        *,
        mode: Mode | None = None,
    ) -> _Write:
        if isinstance(view, YdsModel):
            view = view.to_dict()
        return _Write(view, mode=mode)

    def error(self, text: str) -> _Error:
        return _Error(text)

    def prompt(self, projection: dict | str) -> _Prompt:
        return _Prompt(projection)

    def receive(
        self,
        channel: str | None = None,
        scope: str | None = None,
    ) -> _Receive:
        return _Receive(channel, scope)

    def send(self, channel: str, payload: Any = None, scope: str = "flow") -> _Send:
        return _Send(channel, payload, scope)

    def form(
        self,
        fields: list[dict | _FormFieldDef],
        *,
        title: str = "",
        intro: str = "",
        initial: dict[str, str] | None = None,
        focus: str | None = None,
    ) -> _Form:
        raw = [f.to_dict() if isinstance(f, _FormFieldDef) else f for f in fields]
        return _Form(
            fields=raw,
            title=title,
            intro=intro,
            initial=initial or {},
            focus=focus,
        )


io = _IO()


def write(view, *, mode=None):
    return io.write(view, mode=mode)


def error(text: str) -> _Error:
    return io.error(text)


def prompt(projection: dict | str) -> _Prompt:
    return io.prompt(projection)


def receive(
    channel: str | None = None,
    scope: str | None = None,
) -> _Receive:
    return io.receive(channel, scope)


def send(channel: str, payload: Any = None, scope: str = "flow") -> _Send:
    return io.send(channel, payload, scope)


def form(
    fields: list[dict | _FormFieldDef],
    *,
    title: str = "",
    intro: str = "",
    initial: dict[str, str] | None = None,
    focus: str | None = None,
) -> _Form:
    return io.form(fields, title=title, intro=intro, initial=initial, focus=focus)


__all__ = ["error", "form", "io", "prompt", "receive", "send", "write"]


# ============================================================
# INTERNAL
# ============================================================


def _text_document(text: str) -> dict:
    """Build the wire document for a plain text projection."""
    if not text:
        return Document(header=Header()).to_dict()
    return Document(
        header=Header(),
        blocks=[Text(text=[InlineText(text=text)])],
    ).to_dict()
