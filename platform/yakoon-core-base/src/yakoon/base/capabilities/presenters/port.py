from asyncio import Protocol

from yakoon.base.models.resource import ResourceRef
from yakoon.base.models.stream import OutputStreaming

from .result import PromptResult


class PresenterViews(Protocol):

    async def emit(
        self,
        state: str,
        *,
        stream: OutputStreaming | None = None,
        **data,
    ) -> None: ...


class PresenterInputs(Protocol):
    async def ask(self, state: str, **data) -> PromptResult: ...


class Presenter(Protocol):

    inputs: PresenterInputs
    views: PresenterViews


class PresenterService(Protocol):
    async def create_presenter(self, resource: ResourceRef, session) -> Presenter: ...
