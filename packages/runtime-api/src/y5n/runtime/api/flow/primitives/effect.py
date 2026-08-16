from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.runtime import Event, InputContext

Mode = Literal["replace", "append"]


class Effect:
    """Marker base class for effects.

    Effects describe side effects that the engine applies after a flow step,
    such as emitting output, starting a task, or dispatching a sub-flow.
    """


@dataclass(frozen=True, slots=True)
class EmitView(Effect):
    """Send a projection to the output layer.

    The projection is rendered according to *mode* (replace or append)
    and optionally persisted across steps.

    ``mode=None`` means "resolve automatically": the first output of a
    flow replaces, subsequent ones append. An explicit mode is always
    honored as given.
    """

    view: object
    persist: bool = False
    mode: Mode | None = "replace"
    space: str | None = None
    view_params: dict | None = None
    job_id: str | None = None
    ctx: InputContext | None = None


@dataclass(frozen=True, slots=True)
class EmitEvent(Effect):
    """Push an event onto a channel.

    The event is delivered to flows waiting on the given channel and scope.
    """

    channel: str
    event: Event
    scope: Scope = Scope.FLOW


@dataclass(frozen=True, slots=True)
class Foreground(Effect):
    """Mark the flow as the session's foreground flow.

    A foreground flow receives user input by default.
    """

    flow_id: str | None = None


@dataclass(frozen=True, slots=True)
class Background(Effect):
    """Remove the flow from foreground status.

    The flow continues to run but no longer captures user input.
    """


@dataclass(frozen=True, slots=True)
class StartTask(Effect):
    """Run an OS process as a background task.

    The process runs independently and sends its result (returncode,
    stdout, stderr) to *channel* on the given scope.
    """

    command: str
    channel: str
    scope: Scope = Scope.SESSION
    kwargs: dict = field(default_factory=dict)

    def __init__(
        self, command: str, channel: str, *, scope: Scope = Scope.SESSION, **kwargs
    ):
        if not channel:
            raise ValueError("channel must be a non-empty string")
        object.__setattr__(self, "command", command)
        object.__setattr__(self, "channel", channel)
        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "kwargs", kwargs)


@dataclass(frozen=True, slots=True)
class StartCommand(Effect):
    """Dispatch a runtime command as a sub-flow.

    The sub-flow's projection output is redirected to *channel*
    (SESSION scope). The caller reads the result with receive().
    """

    command: str
    channel: str
    remote: str | None = None

    def __init__(self, command: str, channel: str, remote: str | None = None):
        if not channel:
            raise ValueError("channel must be a non-empty string")
        object.__setattr__(self, "command", command)
        object.__setattr__(self, "channel", channel)
        object.__setattr__(self, "remote", remote)


@dataclass(frozen=True, slots=True)
class CwdEffect(Effect):
    path: str


@dataclass(frozen=True, slots=True)
class FlowStopEffect(Effect):
    flow_id: str


@dataclass(frozen=True, slots=True)
class FlowFgEffect(Effect):
    flow_id: str | None = None
