from y5n.api.nodes import Node

from .runtime import setup
from .runtime.world import world

luma = Node(
    key="luma",
    name="Luma",
    anonymous=True,
    setup=setup,
)

luma.mount(world)
