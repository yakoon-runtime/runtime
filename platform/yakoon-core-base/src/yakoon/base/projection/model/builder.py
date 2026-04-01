from __future__ import annotations

import uuid
from collections.abc import Sequence

from .block import Block, FieldsBlock, TextBlock
from .field import Field
from .header import ErrorKind, Role
from .model import Projection, ProjectionHeader


def _view(
    *,
    blocks: Sequence[Block],
    role: Role = "info",
    title: str | None = None,
    error_kind: ErrorKind | None = None,
    error_code: str | None = None,
    projection_id: str | None = None,
) -> Projection:

    header = ProjectionHeader(
        role=role,
        title=title,
        error_kind=error_kind,
        error_code=error_code,
        meta=None,
    )

    return Projection(
        kind="projection",
        id=projection_id or f"prj.{uuid.uuid4().hex}",
        header=header,
        blocks=list(blocks),
    )


def v_text(
    text: str,
    *,
    role: Role = "info",
    title: str | None = None,
    error_kind: ErrorKind | None = None,
    error_code: str | None = None,
    projection_id: str | None = None,
) -> Projection:
    projection_id = projection_id or f"view.{uuid.uuid4().hex}"
    block_id = f"{projection_id}:b{0}"
    return _view(
        role=role,
        title=title,
        error_kind=error_kind,
        error_code=error_code,
        projection_id=projection_id,
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
    projection_id: str | None = None,
) -> Projection:
    return v_text(text, role="info", title=title, projection_id=projection_id)


def v_error_domain(
    text: str, *, title=None, error_code=None, projection_id=None
) -> Projection:
    return v_text(
        text,
        role="error",
        title=title,
        error_kind="domain",
        error_code=error_code,
        projection_id=projection_id,
    )


def v_error_fatal(
    text: str, *, title=None, error_code=None, projection_id=None
) -> Projection:
    return v_text(
        text,
        role="error",
        title=title,
        error_kind="fatal",
        error_code=error_code,
        projection_id=projection_id,
    )


def v_error_system(
    text: str,
    *,
    title: str | None = None,
    error_kind: ErrorKind = "system",
    error_code: str | None = None,
    projection_id: str | None = None,
) -> Projection:
    return v_text(
        text,
        role="error",
        title=title,
        error_kind=error_kind,
        error_code=error_code,
        projection_id=projection_id,
    )


def v_success(
    text: str,
    *,
    title: str | None = None,
    projection_id: str | None = None,
) -> Projection:
    return v_text(text, role="success", title=title, projection_id=projection_id)


def v_warning(
    text: str,
    *,
    title: str | None = None,
    projection_id: str | None = None,
) -> Projection:
    return v_text(text, role="warning", title=title, projection_id=projection_id)


def v_help(
    text: str,
    *,
    title: str | None = None,
    projection_id: str | None = None,
) -> Projection:
    return v_text(text, role="help", title=title, projection_id=projection_id)


def v_blocks(
    blocks: list[Block],
    *,
    role: Role = "info",
    title: str | None = None,
    error_kind: ErrorKind | None = None,
    projection_id: str | None = None,
) -> Projection:
    return _view(
        blocks=blocks,
        role=role,
        title=title,
        error_kind=error_kind,
        projection_id=projection_id,
    )


def v_fields(
    fields: list[Field],
    *,
    role: Role = "info",
    title: str | None = None,
    projection_id: str | None = None,
) -> Projection:
    return _view(
        role=role,
        title=title,
        projection_id=projection_id,
        blocks=[
            FieldsBlock(
                id="0",
                fields=fields,
            )
        ],
    )
