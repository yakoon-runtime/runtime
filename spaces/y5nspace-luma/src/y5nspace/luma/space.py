from y5n.api.nodes import Node

from .runtime import setup
from .runtime.box import box
from .runtime.nav import connect, dig, enter, entry, go, leave, look
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
luma.mount(look)
luma.mount(go)
luma.mount(dig)
luma.mount(connect)
