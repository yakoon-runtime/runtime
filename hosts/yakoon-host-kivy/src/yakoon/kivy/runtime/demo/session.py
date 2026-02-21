

class DemoSession:

    def __init__(self):
        self._io = None
        self._signals = set()
        self.key = "demo"

    def bind_io(self, io):
        self._io = io

    def has_signal(self, name: str) -> bool:
        return name in self._signals

    def set_signal(self, name: str):
        self._signals.add(name)
