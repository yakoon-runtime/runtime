from typing import Any

from y5n.base.document import DocumentEvent
from y5n.base.document.model.header import DocumentHeader
from y5n.base.document.model.inline import (
    Inline,
    InlineArg,
    InlineBreak,
    InlineCmd,
    InlineCode,
    InlineEm,
    InlineLink,
    InlineMark,
    InlineSelect,
    InlineSpace,
    InlineStrong,
    InlineText,
    InlineUnderline,
)
from y5n.base.document.transfer import (
    DocumentState,
    Patch,
    PatchAppendStructure,
    PatchFinishNode,
    PatchReset,
)
from y5n.base.runtime.input import InputContext, Origin


def deserialize_event(data: dict) -> DocumentEvent:
    return DocumentEvent(
        id=data["id"],
        job_id=data.get("job", "system"),
        header=_deserialize_header(data.get("header")),
        ctx=_deserialize_context(data.get("context")),
        state=_deserialize_state(data.get("state")),
        patch=_deserialize_patch(data["patch"]),
        view_params=data.get("view_params"),
    )


# ------------------------
# Context / State
# ------------------------


def _deserialize_context(data: dict | None) -> InputContext | None:
    if not data:
        return None

    origin_str = data.get("origin")
    origin = Origin(origin_str) if origin_str else Origin.HUMAN
    return InputContext(
        origin=origin,
        channel=data.get("channel"),
        echo=data.get("echo"),
    )


def _deserialize_state(data: dict | None) -> DocumentState | None:
    if not data:
        return None

    return DocumentState(
        node_path=data.get("node_path"),
        user=data.get("user"),
    )


def _deserialize_header(data: dict | None) -> DocumentHeader | None:
    if not data:
        return None

    return DocumentHeader(
        role=data.get("role"),
        title=data.get("title"),
        subtitle=data.get("subtitle"),
        error_kind=data.get("error_kind"),
        error_code=data.get("error_code"),
        meta=data.get("meta"),
    )


# ------------------------
# Patch
# ------------------------


def _deserialize_patch(data: dict) -> Patch:
    ops = [_deserialize_op(op) for op in data["ops"]]

    return Patch(
        ops=ops,
        final=data.get("final", False),
    )


def _deserialize_op(data: dict):
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


def _deserialize_node(data: dict) -> dict:
    props = _reconstruct_inlines(data.get("props", {}))
    return {
        "id": data["id"],
        "type": data["type"],
        "parent": data.get("parent"),
        "depth": data.get("depth", 0),
        "props": props,
    }


INLINE_TYPES = {
    "text": InlineText,
    "code": InlineCode,
    "strong": InlineStrong,
    "em": InlineEm,
    "underline": InlineUnderline,
    "link": InlineLink,
    "arg": InlineArg,
    "mark": InlineMark,
    "cmd": InlineCmd,
    "select": InlineSelect,
    "break": InlineBreak,
    "space": InlineSpace,
}


def _reconstruct_inlines(value: Any) -> Any:
    if isinstance(value, list):
        return [_reconstruct_inlines(v) for v in value]
    if isinstance(value, dict):
        if "type" in value and value["type"] in INLINE_TYPES:
            return _dict_to_inline(value)
        return {k: _reconstruct_inlines(v) for k, v in value.items()}
    return value


def _dict_to_inline(data: dict) -> Inline:
    cls = INLINE_TYPES[data["type"]]
    kwargs = {}
    for field in cls.__dataclass_fields__:
        if field == "type":
            continue
        raw = data.get(field)
        if field == "children" and isinstance(raw, list):
            kwargs[field] = [
                (
                    _dict_to_inline(c)
                    if isinstance(c, dict) and "type" in INLINE_TYPES
                    else _reconstruct_inlines(c)
                )
                for c in raw
            ]
        else:
            kwargs[field] = raw
    return cls(**kwargs)
