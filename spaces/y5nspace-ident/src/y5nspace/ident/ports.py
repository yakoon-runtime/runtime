from typing import Protocol

from y5n.api.projections import Projection

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
