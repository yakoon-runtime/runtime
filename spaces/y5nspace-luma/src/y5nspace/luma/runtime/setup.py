from __future__ import annotations

from y5n.api.nodes import NodeSpace

from ..services.box import MemoryBoxService
from ..services.contracts import BoxService, WorldService
from ..services.world import MemoryWorldService


async def setup(space: NodeSpace):

    worlds = MemoryWorldService()
    boxes = MemoryBoxService()

    # ----------------------------------
    # PORTS
    # ----------------------------------

    space.ports.provide(WorldService, worlds)
    space.ports.provide(BoxService, boxes)
