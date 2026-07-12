from y5n.api.dsl import out
from y5n.api.naming import Key
from y5n.api.nodes import NodeSpace, Request


async def run(space: NodeSpace):
    on_project = space.ports.get("projection.ident")
    identity = space.session.get_identity()

    projection = await on_project(
        name="whoami",
        lang=space.request.lang,
        state={"user": str(identity) if identity else None},
    )

    yield out(projection)
