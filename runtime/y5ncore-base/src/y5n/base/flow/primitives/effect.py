from typing import Literal

from y5n.base.flow.channel import Scope
from y5n.base.runtime import Event

Mode = Literal["replace", "append"]


class Effect:
    pass


class EmitView(Effect):
    def __init__(self, view, persist: bool = False, mode: Mode = "replace", space: str | None = None, view_params: dict | None = None):
        self.view = view
        self.persist = persist
        self.mode = mode
        self.space = space
        self.view_params = view_params


class EmitEvent(Effect):
    def __init__(self, channel: str, event: Event, scope: Scope = Scope.FLOW):
        self.channel = channel
        self.event = event
        self.scope = scope


class Foreground(Effect):
    def __init__(self, flow_id: str | None = None):
        self.flow_id = flow_id


class Background(Effect):
    pass


class StartTask(Effect):
    def __init__(self, command: str, channel: str, **kwargs):
        self.command = command
        self.channel = channel
        self.kwargs = kwargs


class StartCommand(Effect):
    def __init__(self, command: str, channel: str):
        self.command = command
        self.channel = channel
