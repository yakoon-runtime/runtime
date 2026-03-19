from typing import Any, Protocol

from yakoon.base.resources.resource import ResourceRef
from yakoon.base.ui import ViewSpec


class Presenter(Protocol):
    """
    Unified presentation API.

    A presenter renders one state, streams it to the host, may pause on
    interactive blocks, and optionally returns collected values.
    """

    async def view(
        self,
        state: str,
        **data: Any,
    ) -> ViewSpec: ...


class PresenterService(Protocol):
    async def create_presenter(self, resource: ResourceRef, session) -> Presenter: ...
