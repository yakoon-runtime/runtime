from __future__ import annotations

from y5n.api.nodes import NodeSpace

from ..services.box import MemoryBoxService
from ..services.contracts import BoxService, ExitService, WorldService
from ..services.exit import MemoryExitService
from ..services.world import MemoryWorldService


async def setup(space: NodeSpace):

    worlds = MemoryWorldService()
    boxes = MemoryBoxService()
    exits = MemoryExitService()

    space.ports.provide(WorldService, worlds)
    space.ports.provide(BoxService, boxes)
    space.ports.provide(ExitService, exits)
