from uuid import uuid4

from y5n.base.runtime import InputEvent

from .outcome import Outcome


class Effect:
    pass


class EmitView(Effect):
    def __init__(self, view, persist: bool = False):
        self.view = view
        self.persist = persist


class EmitEvent(Effect):
    def __init__(self, channel: str, event: InputEvent):
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
