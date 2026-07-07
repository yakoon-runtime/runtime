from y5n.api.nodes import Node

from .runtime.info import run as info
from .runtime.jobs.space import jobs
from .runtime.labs.space import labs
from .runtime.net.space import net
from .runtime.session.space import session
from .runtime.setup import setup
from .runtime.system.space import system
from .runtime.welcome import run as welcome_run

# ----------------------------------
# SHELL
# ----------------------------------

shell = Node(
    key="shell",
    name="Shell",
    is_shell=True,
    anonymous=True,
    setup=setup,
)

# ----------------------------------
# STATUS
# ----------------------------------

shell.add(
    Node(
        key="info",
        run=info,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# WELCOME
# ----------------------------------

shell.add(
    Node(
        key="welcome",
        run=welcome_run,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)


# ----------------------------------
# MOUNT
# ----------------------------------

shell.mount(system)
shell.mount(jobs)
shell.mount(labs)
shell.mount(net)
shell.mount(session)
