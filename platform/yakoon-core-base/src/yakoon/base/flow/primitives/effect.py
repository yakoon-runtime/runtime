class Effect:
    pass


class Emit(Effect):
    def __init__(self, view):
        self.view = view


class SetFocus(Effect):
    def __init__(self, flow_id):
        self.flow_id = flow_id


class AutoFocus(Effect):
    pass


class ClearFocus(Effect):
    pass
