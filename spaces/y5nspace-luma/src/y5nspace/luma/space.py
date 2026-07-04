from y5n.api.nodes import Node

from .runtime import setup
from .runtime.box import box
from .runtime.nav import enter, entry, leave
from .runtime.world import world

luma = Node(
    key="luma",
    name="Luma",
    anonymous=True,
    setup=setup,
)

luma.mount(world)
luma.mount(box)
luma.mount(enter)
luma.mount(entry)
luma.mount(leave)
