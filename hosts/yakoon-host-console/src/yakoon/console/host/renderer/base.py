from typing import Protocol


class BaseRenderer(Protocol):

    def append(self, key, chunk): ...
    def finish(self): ...
