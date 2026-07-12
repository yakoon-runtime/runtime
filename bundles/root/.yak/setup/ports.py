from typing import Protocol

from y5n.api.ports import Port


class GreetService(Protocol):
    def __call__(self, first_name: str, last_name: str) -> str: ...


GREET = Port("greet", protocol=GreetService)
