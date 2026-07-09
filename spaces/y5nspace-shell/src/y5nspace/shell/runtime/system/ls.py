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
    target_name = space.request.arg(0)

    current_node = space.session.get_current_node()  # type: ignore

    if target_name:
        scope = str(current_node) + "/" + target_name
    else:
        scope = str(current_node)

    current_path = str(current_node)

    on_source = space.ports.get(OnSourceRead)
    result = await on_source(DataRequest(f"system:nodes --scope {scope}"))

    commands = []
    spaces = []

    # local if the node is a direct child of the current scope,
    # global if it is inherited from a parent or sibling scope

    for x in result.rows:
        path = str(x.get("path", ""))
        parent_path = path.rsplit("/", 1)[0] if "/" in path else ""
        if not parent_path:
            parent_path = "/"
        x["variant"] = "local" if parent_path == current_path else "global"

        if x["navigable"]:
            if not x.get("resolvable", True):
                x["variant"] = "container"
            spaces.append(x)
        else:
            commands.append(x)

    if not show_all:
        commands = [c for c in commands if c["variant"] != "global"]
        spaces = [s for s in spaces if s["variant"] != "global"]

    commands.sort(key=lambda i: i["key"])
    spaces.sort(key=lambda i: i["key"])

    projection = await space.ports.get(OnProject)(
        name="system/ls",
        lang=space.session.lang,
        state={
            "commands": commands,
            "spaces": spaces,
        },
    )

    yield out(projection)
