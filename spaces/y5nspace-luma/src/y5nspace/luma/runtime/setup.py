from __future__ import annotations

from y5n.api.nodes import NodeSpace

from ..services.contracts import WorldService
from ..services.world import MemoryWorldService


async def setup(space: NodeSpace):

    worlds = MemoryWorldService()

    # ----------------------------------
    # PORTS
    # ----------------------------------

    space.ports.provide(WorldService, worlds)
    space.ports.provide("IWorldService", worlds)
