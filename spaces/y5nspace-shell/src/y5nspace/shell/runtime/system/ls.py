from y5n.api.data import DataRequest
from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnSourceRead

from ...ports import OnProject

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    show_all = space.request.has_option("all")

    current_node = space.session.get_current_node()  # type: ignore
    current_path = str(current_node)

    on_source = space.ports.get(OnSourceRead)
    result = await on_source(DataRequest(f"system:nodes --scope {current_node}"))

    commands = []
    spaces = []
    for x in result.rows:
        path = str(x.get("path", ""))
        if x["scope"] == "global" and not (current_path != "/" and path.startswith(current_path)):
            x["variant"] = "global"
        else:
            x["variant"] = "local"

        if x["navigable"]:
            spaces.append(x)
        else:
            commands.append(x)

    if not show_all:
        commands = [c for c in commands if c["variant"] != "global"]
        spaces = [s for s in spaces if s["variant"] != "global"]

    commands.sort(key=lambda i: i["key"])
    spaces.sort(key=lambda i: i["key"])

    projection = await space.ports.get(OnProject)(
        name="list/overview",
        lang=space.session.lang,
        state={
            "commands": commands,
            "spaces": spaces,
        },
    )

    yield out(projection)
