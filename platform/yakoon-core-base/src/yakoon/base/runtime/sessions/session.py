from typing import Protocol

from yakoon.base.capabilities.identity import PermissionSet
from yakoon.base.ui import View, ViewEvent
from yakoon.base.values import Key


class Session(Protocol):

    @property
    def lang(self) -> str: ...

    @property
    def key(self) -> Key: ...

    @property
    def permissions(self) -> PermissionSet: ...

    async def emit(
        self,
        payload: View | ViewEvent,
        *,
        job_id: str | None = None,
        channel: str = "main",
    ) -> None: ...
