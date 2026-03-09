from __future__ import annotations

from collections.abc import Sequence

from .blocks import Block, FieldsBlock, InputMode, TextBlock
from .document import ErrorKind, Role, ViewSpec
from .fields import ViewFieldDef


def _view(
    *,
    blocks: Sequence[Block],
    role: Role = "info",
    title: str | None = None,
    error_kind: ErrorKind | None = None,
    view_id: str | None = None,
) -> ViewSpec:
    return ViewSpec(
        kind="view",
        id=view_id,
        role=role,
        title=title,
        blocks=list(blocks),
        error_kind=error_kind,
        meta=None,
    )


def v_text(
    text: str,
    *,
    role: Role = "info",
    title: str | None = None,
    error_kind: ErrorKind | None = None,
    view_id: str | None = None,
) -> ViewSpec:
    return _view(
        role=role,
        title=title,
        error_kind=error_kind,
        view_id=view_id,
        blocks=[TextBlock(text=text)],
    )


def v_info(
    text: str,
    *,
    title: str | None = None,
    view_id: str | None = None,
) -> ViewSpec:
    return v_text(text, role="info", title=title, view_id=view_id)


def v_error(
    text: str,
    *,
    title: str | None = None,
    error_kind: ErrorKind = "system",
    view_id: str | None = None,
) -> ViewSpec:
    return v_text(
        text,
        role="error",
        title=title,
        error_kind=error_kind,
        view_id=view_id,
    )


def v_success(
    text: str,
    *,
    title: str | None = None,
    view_id: str | None = None,
) -> ViewSpec:
    return v_text(text, role="success", title=title, view_id=view_id)


def v_warning(
    text: str,
    *,
    title: str | None = None,
    view_id: str | None = None,
) -> ViewSpec:
    return v_text(text, role="warning", title=title, view_id=view_id)


def v_help(
    text: str,
    *,
    title: str | None = None,
    view_id: str | None = None,
) -> ViewSpec:
    return v_text(text, role="help", title=title, view_id=view_id)


def v_blocks(
    blocks: list[Block],
    *,
    role: Role = "info",
    title: str | None = None,
    error_kind: ErrorKind | None = None,
    view_id: str | None = None,
) -> ViewSpec:
    return _view(
        blocks=blocks,
        role=role,
        title=title,
        error_kind=error_kind,
        view_id=view_id,
    )


def v_fields(
    fields: list[ViewFieldDef],
    *,
    input_mode: InputMode,
    role: Role = "info",
    title: str | None = None,
    view_id: str | None = None,
) -> ViewSpec:
    return _view(
        role=role,
        title=title,
        view_id=view_id,
        blocks=[
            FieldsBlock(
                fields=fields,
                input_mode=input_mode,
            )
        ],
    )
