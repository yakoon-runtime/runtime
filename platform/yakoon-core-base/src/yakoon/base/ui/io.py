from collections.abc import Callable
from typing import Protocol

from .event import ViewEvent

RenderDone = Callable[[], None]


class IO(Protocol):

    async def view(
        self,
        event: ViewEvent,
        done: RenderDone,
    ) -> None: ...
