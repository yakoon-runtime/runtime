from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from yakoon.base.resources.resource import ResourceRef

    from .view import PresenterView


class Presenter(Protocol):
    """
    Unified presentation API.

    A presenter renders one state, streams it to the host, may pause on
    interactive blocks, and optionally returns collected values.
    """

    async def render(
        self,
        state: str,
        **data: Any,
    ) -> PresenterView: ...


class PresenterService(Protocol):
    async def create_presenter(self, resource: ResourceRef, session) -> Presenter: ...
