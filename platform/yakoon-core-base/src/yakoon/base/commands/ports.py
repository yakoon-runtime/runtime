from typing import Protocol

from yakoon.base.projection import Projection

# ----------------------------------
# COMMAND PORTS
# ----------------------------------


class OnProjectCmd(Protocol):
    async def __call__(self, *, name: str, state: dict | None = None) -> Projection: ...
