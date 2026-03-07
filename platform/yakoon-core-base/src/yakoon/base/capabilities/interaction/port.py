from asyncio import Event, Future
from collections.abc import Awaitable, Callable
from typing import Protocol

from yakoon.base.capabilities.presenters import PromptResult
from yakoon.base.runtime import Session
from yakoon.base.ui import ViewSpec

from .types import DialogState


class InputService(Protocol):

    async def ask_view(self, session: Session, field: ViewSpec) -> PromptResult: ...


class DialogService(Protocol):

    def state(self, session: Session) -> DialogState: ...
    def edge_event(self, session: Session) -> Event: ...

    def resolve_input(self, session: Session, values: dict[str, object]) -> bool: ...
    def cancel_input(self, session: Session) -> None: ...
    def cleanup(self, session: Session) -> None: ...

    def is_waiting(self, session: Session) -> bool: ...
    def get_view(self, session: Session) -> ViewSpec: ...
    def wait_view(
        self,
        session: Session,
        *,
        view: ViewSpec,
        timeout: float | None = None,
        on_timeout: Callable[[], Awaitable[None]] | None = None,
    ) -> Future: ...
