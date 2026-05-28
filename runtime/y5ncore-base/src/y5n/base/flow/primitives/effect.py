from y5n.base.runtime import InputEvent


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
