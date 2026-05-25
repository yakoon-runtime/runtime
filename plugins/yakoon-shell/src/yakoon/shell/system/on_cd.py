from yakoon.api.data import DataRequest
from yakoon.api.nodes import NodePath, NodeSpace
from yakoon.api.ports import OnSourceRead

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_cd(space: NodeSpace):

    target = space.request.arg(0)
    if not target:
        return

    on_source = space.ports.get(OnSourceRead)

    # ----------------------------------
    # CURRENT RUNTIME SPACE
    # ----------------------------------

    current_path = space.session.get_current_node()

    # ----------------------------------
    # ROOT
    # ----------------------------------

    if target == "/":
        space.session.set_current_node(NodePath.root())
        return

    # ----------------------------------
    # PARENT
    # ----------------------------------

    if target == "..":
        parent = current_path.parent
        if parent:
            space.session.set_current_node(parent)

        return

    # ----------------------------------
    # PATH
    # ----------------------------------

    path = NodePath.from_string(target)

    # Absolute navigation.
    if target.startswith("/"):
        resolved_path = path

    # Relative navigation.
    else:
        resolved_path = current_path.join(path)

    # ----------------------------------
    # RESOLVE TARGET
    # ----------------------------------

    target_result = await on_source(
        DataRequest(f"system:nodes --by-key {resolved_path}")
    )

    if target_result.status != "ok":
        return

    target_node = target_result.one()

    # ----------------------------------
    # NAVIGABLE
    # ----------------------------------

    if not target_node["navigable"]:
        return

    # ----------------------------------
    # ACTIVATE RUNTIME SPACE
    # ----------------------------------

    space.session.set_current_node(resolved_path)
