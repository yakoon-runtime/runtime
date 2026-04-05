from yakoon.base.projection.transport.patch import (
    PatchAppendStructure,
    PatchAppendText,
    PatchFinishNode,
    PatchReset,
)


def serialize_event(event):
    document = {
        "id": event.id,
        "job": event.job_id,
        "header": serialize_header(event.header),
        "patch": serialize_patch(event.patch),
        "final": event.patch.final,
    }
    return document


def serialize_header(header):
    if not header:
        return None

    return {
        "role": header.role,
        "title": header.title,
        "subtitle": header.subtitle,
        "error_kind": header.error_kind,
        "error_code": header.error_code,
    }


def serialize_patch(patch):
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
    if isinstance(op, PatchAppendText):
        return {
            "op": "append_text",
            "block_id": op.block_id,
            "key": op.key,
            "text": op.text,
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

        for field in value.__dataclass_fields__:
            result[field] = to_json_safe(getattr(value, field))

        return result

    # fallback (nur noch echte edge cases)
    return str(value)
