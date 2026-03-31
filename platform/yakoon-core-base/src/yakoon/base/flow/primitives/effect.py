from yakoon.base.runtime import InputEvent


class Effect:
    pass


class EmitView(Effect):
    def __init__(self, view):
        self.view = view


class EmitEvent(Effect):
    def __init__(self, channel: str, event: InputEvent):
        self.channel = channel
        self.event = event


class SetFocus(Effect):
    def __init__(self, flow_id):
        self.flow_id = flow_id


class AutoFocus(Effect):
    pass


class ClearFocus(Effect):
    pass
