from typing import Any, Protocol

from yakoon.base.resources.resource import ResourceRef
from yakoon.base.ui.stream import OutputStreaming

from .result import PresentResult


class Presenter(Protocol):
    """
    Unified presentation API.

    A presenter renders one state, streams it to the host, may pause on
    interactive blocks, and optionally returns collected values.
    """

    async def present(
        self,
        state: str,
        *,
        stream: OutputStreaming | None = None,
        **data: Any,
    ) -> PresentResult | None: ...

    async def require_present(
        self,
        state: str,
        *,
        stream: OutputStreaming | None = None,
        **data: Any,
    ) -> PresentResult: ...

    async def require_first(
        self,
        state: str,
        *,
        stream: OutputStreaming | None = None,
        **data: Any,
    ) -> Any: ...


class PresenterService(Protocol):
    async def create_presenter(self, resource: ResourceRef, session) -> Presenter: ...
