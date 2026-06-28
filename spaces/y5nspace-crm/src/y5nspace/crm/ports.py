from typing import Protocol

from y5n.base.projection import Projection


class OnProject(Protocol):
    async def __call__(
        self,
        *,
        name: str,
        lang: str,
        state: dict | None = None,
    ) -> Projection: ...
