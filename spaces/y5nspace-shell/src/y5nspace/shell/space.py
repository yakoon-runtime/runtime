from y5n.api.nodes import Node

from .runtime.ident.space import ident
from .runtime.jobs.space import jobs
from .runtime.labs.space import labs
from .runtime.net.space import net
from .runtime.session.space import session
from .runtime.setup import setup

# ----------------------------------
# SHELL
# ----------------------------------

shell = Node(
    key="shell",
    name="Shell",
    anonymous=True,
    resolvable=False,
    navigable=True,
    setup=setup,
)


# ----------------------------------
# MOUNT
# ----------------------------------

shell.mount(jobs)
shell.mount(labs)
shell.mount(net)
shell.mount(session)
shell.mount(ident)
