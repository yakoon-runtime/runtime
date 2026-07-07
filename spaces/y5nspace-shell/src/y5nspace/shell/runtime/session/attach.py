from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnSessionAttach
from y5n.api.projections import to_text


async def run(space: NodeSpace):

    target = space.request.arg(0)
    if not target:
        yield out(to_text("Usage: session attach <key>"))
        return

    on_attach = space.ports.get(OnSessionAttach)
    await on_attach(session=space.session, target_key=target)

    yield out(to_text(f"Attached to session {target}"))
