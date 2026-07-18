from y5n.base.document import DocumentEvent
from y5n.base.document.transfer import (
    DocumentState,
    PatchAppendStructure,
    PatchFinishNode,
    PatchReset,
)
from y5n.base.runtime.input import InputContext


def serialize_event(event: DocumentEvent):
    document = {
        "id": event.id,
        "job": event.job_id,
        "header": _serialize_header(event.header),
        "context": _serialize_context(event.ctx),
        "state": _serialize_state(event.state),
        "patch": _serialize_patch(event.patch),
        "view_params": event.view_params,
        "final": event.patch.final,
    }
    return document


def _serialize_context(context: InputContext | None) -> dict | None:
    if context is None:
        return None

    data: dict[str, object] = {
        "origin": context.origin.value,
    }
    if context.channel is not None:
        data["channel"] = context.channel
    if context.echo is not None:
        data["echo"] = context.echo

    return data


def _serialize_state(state: DocumentState | None) -> dict | None:
    if state is None:
        return None

    data: dict[str, object] = {}
    if state.node_path is not None:
        data["node_path"] = state.node_path
    if state.user is not None:
        data["user"] = state.user

    return data or None


def _serialize_header(header):
    if not header:
        return None

    return {
        "role": header.role,
        "title": header.title,
        "subtitle": header.subtitle,
        "error_kind": header.error_kind,
        "error_code": header.error_code,
    }


def _serialize_patch(patch):
    return {
        "ops": [serialize_op(op) for op in patch.ops],
        "final": patch.final,
    }


def serialize_op(op):

    if isinstance(op, PatchReset):
        return {"op": "reset"}

    if isinstance(op, PatchAppendStructure):
        return {
            "op": "append_structure",
            "nodes": [serialize_node(n) for n in op.nodes],
        }
    if isinstance(op, PatchFinishNode):
        return {
            "op": "finish_node",
            "block_id": op.block_id,
        }


def serialize_node(n):
    return {
        "id": n.id,
        "type": n.type,
        "parent": n.parent,
        "depth": n.depth,
        "props": serialize_props(n.props),
    }


def serialize_props(props):
    result = {}

    for k, v in props.items():
        # recursive explosions!
        if k in ("block", "blocks", "items"):
            continue

        result[k] = to_json_safe(v)

    return result


def to_json_safe(value):
    # primitive
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    # list
    if isinstance(value, list):
        return [to_json_safe(v) for v in value]

    # dict
    if isinstance(value, dict):
        return {k: to_json_safe(v) for k, v in value.items()}

    # Inline (dataclass!)
    if hasattr(value, "__dataclass_fields__"):
        result = {}

        result["type"] = value.__class__.__name__.replace("Inline", "").lower()

        for field in value.__dataclass_fields__:
            result[field] = to_json_safe(getattr(value, field))

        return result

    # fallback (nur noch echte edge cases)
    return str(value)
