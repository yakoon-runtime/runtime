from __future__ import annotations


class Outcome:
    def __init__(self, control=None, effects=None, value=None):
        self.control = control
        self.effects = effects or []
        self.value = value
