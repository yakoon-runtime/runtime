from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from y5n.base.flow.channel import Scope
from y5n.base.runtime import Event, InputContext

Mode = Literal["replace", "append"]


class Effect:
    """Marker base class for effects.

    Effects describe side effects that the engine applies after a flow step,
    such as emitting output, starting a task, or dispatching a sub-flow.
    """


@dataclass(slots=True)
class EmitView(Effect):
    """Send a projection to the output layer.

    The projection is rendered according to *mode* (replace or append)
    and optionally persisted across steps.
    """

    view: object
    persist: bool = False
    mode: Mode = "replace"
    space: str | None = None
    view_params: dict | None = None
    job_id: str | None = None
    ctx: InputContext | None = None


@dataclass(slots=True)
class EmitEvent(Effect):
    """Push an event onto a channel.

    The event is delivered to flows waiting on the given channel and scope.
    """

    channel: str
    event: Event
    scope: Scope = Scope.FLOW


@dataclass(slots=True)
class Foreground(Effect):
    """Mark the flow as the session's foreground flow.

    A foreground flow receives user input by default.
    """

    flow_id: str | None = None


@dataclass(slots=True)
class Background(Effect):
    """Remove the flow from foreground status.

    The flow continues to run but no longer captures user input.
    """


class StartTask(Effect):
    """Run an OS process as a background task.

    The process runs independently and sends its result (returncode,
    stdout, stderr) to *channel* on the given scope.
    """

    def __init__(
        self, command: str, channel: str, *, scope: Scope = Scope.SESSION, **kwargs
    ):
        if not channel:
            raise ValueError("channel must be a non-empty string")
        self.command = command
        self.channel = channel
        self.scope = scope
        self.kwargs = kwargs


class StartCommand(Effect):
    """Dispatch a runtime command as a sub-flow.

    The sub-flow's projection output is redirected to *channel*
    (SESSION scope). The caller reads the result with receive().
    """

    def __init__(self, command: str, channel: str, remote: str | None = None):
        if not channel:
            raise ValueError("channel must be a non-empty string")
        self.command = command
        self.channel = channel
        self.remote = remote
