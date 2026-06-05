from y5n.base.projection import ProjectionEvent
from y5n.base.projection.transfer import (
    Patch,
    PatchAppendStructure,
    PatchFinishNode,
    PatchReset,
    ProjectionState,
)
from y5n.base.projection.transfer.node import Node
from y5n.base.runtime.input import InputContext


def deserialize_event(data: dict) -> ProjectionEvent:
    return ProjectionEvent(
        id=data["id"],
        job_id=data.get("job"),
        header=_deserialize_header(data.get("header")),
        ctx=_deserialize_context(data.get("context")),
        state=_deserialize_state(data.get("state")),
        patch=_deserialize_patch(data["patch"]),
    )


# ------------------------
# Context / State
# ------------------------


def _deserialize_context(data):
    if not data:
        return None

    return InputContext(
        origin=data.get("origin"),
    )


def _deserialize_state(data):
    if not data:
        return None

    return ProjectionState(
        node_path=data.get("node_path"),
        user=data.get("user"),
    )


def _deserialize_header(data):
    if not data:
        return None

    # ggf. eigene Header-Klasse nutzen
    return type("Header", (), data)()


# ------------------------
# Patch
# ------------------------


def _deserialize_patch(data):
    ops = [_deserialize_op(op) for op in data["ops"]]

    return Patch(
        ops=ops,
        final=data.get("final", False),
    )


def _deserialize_op(data):
    op_type = data["op"]

    if op_type == "reset":
        return PatchReset()

    if op_type == "append_structure":
        return PatchAppendStructure(
            nodes=[_deserialize_node(n) for n in data["nodes"]],
        )

    if op_type == "finish_node":
        return PatchFinishNode(
            block_id=data["block_id"],
        )

    raise ValueError(f"Unknown op: {op_type}")


# ------------------------
# Nodes
# ------------------------


def _deserialize_node(data):
    return Node(
        id=data["id"],
        type=data["type"],
        parent=data.get("parent"),
        depth=data.get("depth"),
        props=data.get("props", {}),
    )
