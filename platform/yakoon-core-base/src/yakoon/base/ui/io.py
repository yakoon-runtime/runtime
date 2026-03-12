from collections.abc import Callable
from typing import Protocol

from .event import ViewEvent

Done = Callable[[], None]


class FlowControl(Protocol):

    def acquire(self) -> None: ...
    def try_acquire(self) -> bool: ...
    def release(self) -> None: ...


class IO(Protocol):

    async def view(
        self,
        event: ViewEvent,
    ) -> None: ...

    def set_flow_control(
        self,
        flow: FlowControl,
    ) -> None: ...
