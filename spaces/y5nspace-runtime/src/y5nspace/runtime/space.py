from y5n.api.nodes import Node, NodeScope

from .runtime.jobs.space import jobs
from .runtime.labs.space import labs
from .runtime.net.space import net
from .runtime.setup import setup
from .runtime.version import run as version
from .runtime.welcome import run as welcome

# ----------------------------------
# RUNTIME
# ----------------------------------

runtime = Node(
    key="runtime",
    name="Runtime",
    setup=setup,
    anonymous=True,
)


# ----------------------------------
# WELCOME
# ----------------------------------

runtime.add(
    Node(
        key="welcome",
        run=welcome,
        anonymous=True,
        scope=NodeScope.NODE,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# VERSION
# ----------------------------------

runtime.add(
    Node(
        key="version",
        run=version,
        anonymous=True,
        scope=NodeScope.NODE,
        resolvable=True,
        navigable=False,
    )
)

runtime.mount(labs)
runtime.mount(jobs)
runtime.mount(net)
