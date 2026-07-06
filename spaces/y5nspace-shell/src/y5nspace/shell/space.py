from y5n.api.nodes import Node

from .runtime.setup import setup
from .runtime.jobs.space import jobs
from .runtime.labs.space import labs
from .runtime.net.space import net
from .runtime.session.space import session
from .runtime.status import run as status_run
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

shell.mount(system)
shell.mount(jobs)
shell.mount(labs)
shell.mount(net)
shell.mount(session)

shell.add(
    Node(
        key="status",
        run=status_run,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)

shell.add(
    Node(
        key="welcome",
        run=welcome_run,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)

