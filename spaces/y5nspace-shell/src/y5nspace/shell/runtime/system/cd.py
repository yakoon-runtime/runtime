from y5n.api.data import DataRequest
from y5n.api.dsl import out_text
from y5n.api.nodes import NodePath, NodeSpace
from y5n.api.ports import OnSourceRead

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    target = space.request.arg(0)
    if not target:
        return

    on_source = space.ports.get(OnSourceRead)

    # ----------------------------------
    # CURRENT RUNTIME SPACE
    # ----------------------------------

    current_path = space.session.get_current_node()  # type: ignore

    # ----------------------------------
    # ROOT
    # ----------------------------------

    if target == "/":
        space.session.set_current_node(NodePath.root())  # type: ignore
        yield out_text("OK.")
        return

    # ----------------------------------
    # PARENT
    # ----------------------------------

    if target == "..":
        parent = current_path.parent
        if parent:
            space.session.set_current_node(parent)  # type: ignore

        yield out_text("OK.")
        return

    # ----------------------------------
    # PATH
    # ----------------------------------

    path = NodePath.from_string(target)

    # Absolute navigation.
    resolved_path = ""
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
    new_path = target_node["path"]
    space.session.set_current_node(new_path)  # type: ignore

    yield out_text("OK.")
