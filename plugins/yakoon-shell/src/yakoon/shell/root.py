from yakoon.base.flow.dsl import out
from yakoon.base.nodes import (
    Node,
    NodeScope,
    RuntimeContext,
)
from yakoon.base.projection.model.model import to_text
from yakoon.shell.nodes import run_welcome


async def run_ls(ctx: RuntimeContext):
    projection = to_text("ls ...")
    yield out(projection)


async def run_version(ctx: RuntimeContext):
    projection = to_text("version ...")
    yield out(projection)


async def run_shell(ctx: RuntimeContext):
    projection = to_text("shell ...")
    yield out(projection)


async def boot_shell(ctx: RuntimeContext):
    projection = to_text("register services ...")
    yield out(projection)


# ----------------------------------
# BUILD RUNTIME TREE
# ----------------------------------

shell = Node(
    key="shell",
    name="Shell",
    is_shell=True,
    anonymous=True,
    run=run_shell,
    setup=boot_shell,
)

shell.add(
    Node(
        key="welcome",
        run=run_welcome,
        anonymous=True,
        scope=NodeScope.NODE,
    )
)

shell.add(
    Node(
        key="ls",
        run=run_ls,
        anonymous=True,
        scope=NodeScope.GLOBAL,
    )
)
shell.add(Node(key="version", run=run_version))
