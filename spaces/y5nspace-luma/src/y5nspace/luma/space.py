from y5n.api.nodes import Node

from .runtime import setup
from .runtime.box import box
from .runtime.exit import exit_node
from .runtime.nav import (
    connect,
    dig,
    drop,
    enter,
    entry,
    go,
    inspect,
    inv,
    leave,
    look,
    move,
    place,
    take,
)
from .runtime.note import note_node
from .runtime.world import world

luma = Node(
    key="luma",
    name="Luma",
    anonymous=True,
    setup=setup,
)

# ----------------------------------
# MOUNT SPACES
# ----------------------------------

luma.mount(world)
luma.mount(box)
luma.mount(exit_node)
luma.mount(note_node)

# ----------------------------------
# MOUNT NODES
# ----------------------------------

luma.mount(enter)
luma.mount(entry)
luma.mount(leave)
luma.mount(look)
luma.mount(go)
luma.mount(dig)
luma.mount(connect)
luma.mount(place)
luma.mount(move)
luma.mount(take)
luma.mount(drop)
luma.mount(inv)
luma.mount(inspect)
