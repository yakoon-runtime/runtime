from yakoon.base.nodes import NodePath, RuntimeContext
from yakoon.base.sources import DataRequest, OnDataSource

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_cd(ctx: RuntimeContext):

    target = ctx.request.arg(0)

    on_source = ctx.ports.get(OnDataSource)

    # ----------------------------------
    # CURRENT RUNTIME SPACE
    # ----------------------------------

    current_path = ctx.session.get_current_node()

    # ----------------------------------
    # ROOT
    # ----------------------------------

    if target == "/":
        ctx.session.set_current_node(NodePath.root())
        return

    # ----------------------------------
    # PARENT
    # ----------------------------------

    if target == "..":
        parent = current_path.parent
        if parent:
            ctx.session.set_current_node(parent)

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

    ctx.session.set_current_node(resolved_path)
