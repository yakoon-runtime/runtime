from __future__ import annotations

import uuid
from collections.abc import Sequence

from .block import Block, FieldsBlock, InputMode, TextBlock
from .field import Field
from .view import ErrorKind, Role, View, ViewHeader


def _view(
    *,
    blocks: Sequence[Block],
    role: Role = "info",
    title: str | None = None,
    error_kind: ErrorKind | None = None,
    view_id: str | None = None,
) -> View:

    header = ViewHeader(
        role=role,
        title=title,
        error_kind=error_kind,
        meta=None,
    )

    return View(
        kind="view",
        id=view_id or f"view.{uuid.uuid4().hex}",
        header=header,
        blocks=list(blocks),
    )


def v_text(
    text: str,
    *,
    role: Role = "info",
    title: str | None = None,
    error_kind: ErrorKind | None = None,
    view_id: str | None = None,
) -> View:
    view_id = view_id or f"view.{uuid.uuid4().hex}"
    block_id = f"{view_id}:b{0}"
    return _view(
        role=role,
        title=title,
        error_kind=error_kind,
        view_id=view_id,
        blocks=[
            TextBlock(
                text=text,
                id=block_id,
            )
        ],
    )


def v_info(
    text: str,
    *,
    title: str | None = None,
    view_id: str | None = None,
) -> View:
    return v_text(text, role="info", title=title, view_id=view_id)


def v_error(
    text: str,
    *,
    title: str | None = None,
    error_kind: ErrorKind = "system",
    view_id: str | None = None,
) -> View:
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
) -> View:
    return v_text(text, role="success", title=title, view_id=view_id)


def v_warning(
    text: str,
    *,
    title: str | None = None,
    view_id: str | None = None,
) -> View:
    return v_text(text, role="warning", title=title, view_id=view_id)


def v_help(
    text: str,
    *,
    title: str | None = None,
    view_id: str | None = None,
) -> View:
    return v_text(text, role="help", title=title, view_id=view_id)


def v_blocks(
    blocks: list[Block],
    *,
    role: Role = "info",
    title: str | None = None,
    error_kind: ErrorKind | None = None,
    view_id: str | None = None,
) -> View:
    return _view(
        blocks=blocks,
        role=role,
        title=title,
        error_kind=error_kind,
        view_id=view_id,
    )


def v_fields(
    fields: list[Field],
    *,
    input_mode: InputMode,
    role: Role = "info",
    title: str | None = None,
    view_id: str | None = None,
) -> View:
    return _view(
        role=role,
        title=title,
        view_id=view_id,
        blocks=[
            FieldsBlock(
                id="0",
                fields=fields,
                input_mode=input_mode,
            )
        ],
    )
