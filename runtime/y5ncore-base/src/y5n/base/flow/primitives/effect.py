from typing import Literal
from uuid import uuid4

from y5n.base.runtime import Event

from .outcome import Outcome

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
    def __init__(self, channel: str, event: Event):
        self.channel = channel
        self.event = event


class Foreground(Effect):
    def __init__(self, flow_id: str | None = None):
        self.flow_id = flow_id


class Background(Effect):
    pass


class TaskHandle:
    def __init__(self, command: str, **kwargs):
        self.task_id = uuid4().hex[:8]
        self.channel = f"task:{self.task_id}"
        self.command = command
        self.kwargs = kwargs

    async def run(self, flow):
        return Outcome(effects=[StartTask(self)])


class StartTask(Effect):
    def __init__(self, handle: TaskHandle):
        self.handle = handle
