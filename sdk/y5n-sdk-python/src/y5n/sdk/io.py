from __future__ import annotations

from y5n.runtime.api.host.protocol import Marker, MarkerKind
from y5n.sdk.models import Field as _FormFieldDef
from y5n.sdk.models import YdsModel


class _Write:
    __slots__ = ("_view", "_mode")

    def __init__(self, view: dict | str, mode: str | None = None) -> None:
        self._view = view
        self._mode = mode

    def __await__(self):
        value: object = (self._view, self._mode) if self._mode else self._view
        yield Marker(MarkerKind.WRITE, value)


class _Error:
    __slots__ = ("_text",)

    def __init__(self, text: str) -> None:
        self._text = text

    def __await__(self):
        yield Marker(MarkerKind.ERROR, self._text)


class _Prompt:
    __slots__ = ("_projection",)

    def __init__(self, projection: dict | str) -> None:
        self._projection = projection

    def __await__(self):
        result = yield Marker(MarkerKind.PROMPT, self._projection)
        return result


class _Receive:
    __slots__ = ("_params",)

    def __init__(self, channel: str | None = None, scope: str | None = None) -> None:
        self._params = {"channel": channel, "scope": scope}

    def __await__(self):
        event = yield Marker(MarkerKind.RECEIVE, self._params)
        return event


class _Form:
    __slots__ = ("_params",)

    def __init__(self, **params: Any) -> None:
        self._params = params

    def __await__(self):
        result = yield Marker(MarkerKind.FORM, self._params)
        return result


class _Send:
    __slots__ = ("_params",)

    def __init__(self, channel: str, payload: Any = None, scope: str = "flow") -> None:
        self._params = {"channel": channel, "payload": payload, "scope": scope}

    def __await__(self):
        yield Marker(MarkerKind.SEND, self._params)


class _IO:
    def write(
        self,
        view: YdsModel | dict | str,
        *,
        mode: str | None = None,
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
