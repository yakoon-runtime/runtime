from typing import Literal

from y5n.base.flow.channel import Scope
from y5n.base.runtime import Event

Mode = Literal["replace", "append"]


class Effect:
    """Marker base class for effects.

    Effects describe side effects that the engine applies after a flow step,
    such as emitting output, starting a task, or dispatching a sub-flow.
    """


class EmitView(Effect):
    """Send a projection to the output layer.

    The projection is rendered according to *mode* (replace or append)
    and optionally persisted across steps.
    """

    def __init__(self, view, persist: bool = False, mode: Mode = "replace", space: str | None = None, view_params: dict | None = None):
        self.view = view
        self.persist = persist
        self.mode = mode
        self.space = space
        self.view_params = view_params


class EmitEvent(Effect):
    """Push an event onto a channel.

    The event is delivered to flows waiting on the given channel and scope.
    """

    def __init__(self, channel: str, event: Event, scope: Scope = Scope.FLOW):
        self.channel = channel
        self.event = event
        self.scope = scope


class Foreground(Effect):
    """Mark the flow as the session's foreground flow.

    A foreground flow receives user input by default.
    """

    def __init__(self, flow_id: str | None = None):
        self.flow_id = flow_id


class Background(Effect):
    """Remove the flow from foreground status.

    The flow continues to run but no longer captures user input.
    """


class StartTask(Effect):
    """Run an OS process as a background task.

    The process runs independently and sends its result (returncode,
    stdout, stderr) to *channel* (SESSION scope).
    """

    def __init__(self, command: str, channel: str, **kwargs):
        if not channel:
            raise ValueError("channel must be a non-empty string")
        self.command = command
        self.channel = channel
        self.kwargs = kwargs


class StartCommand(Effect):
    """Dispatch a runtime command as a sub-flow.

    The sub-flow's projection output is redirected to *channel*
    (SESSION scope). The caller reads the result with receive().
    """

    def __init__(self, command: str, channel: str):
        if not channel:
            raise ValueError("channel must be a non-empty string")
        self.command = command
        self.channel = channel
