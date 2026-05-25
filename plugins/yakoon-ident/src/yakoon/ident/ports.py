from typing import Protocol

from yakoon.base.projection import Projection

# -------------
# --- PORTS ---
# -------------


class OnProject(Protocol):
    async def __call__(
        self,
        *,
        name: str,
        lang: str,
        state: dict | None = None,
    ) -> Projection: ...
