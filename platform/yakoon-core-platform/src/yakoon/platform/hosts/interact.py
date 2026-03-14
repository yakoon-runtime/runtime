from typing import Protocol


class Interaction(Protocol):

    def add_history(self, command: str) -> None: ...
