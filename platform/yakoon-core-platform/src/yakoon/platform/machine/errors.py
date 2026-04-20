from __future__ import annotations

from yakoon.base.flow.primitives import create_projection
from yakoon.base.projection.model import (
    ErrorKind,
    InlineText,
    Projection,
    Role,
    TextBlock,
)

# ---------------------------------------------------------
# ERROR API
# ---------------------------------------------------------


def domain_error_projection(text: str, *, title=None, error_code=None) -> Projection:
    return _p_text(
        text,
        role="error",
        title=title,
        error_kind="domain",
        error_code=error_code,
    )


def system_error_projection(
    text: str,
    *,
    title: str | None = None,
    error_kind: ErrorKind = "system",
    error_code: str | None = None,
) -> Projection:
    return _p_text(
        text,
        role="error",
        title=title,
        error_kind=error_kind,
        error_code=error_code,
    )


def fatal_error_projection(
    text: str,
    *,
    title=None,
    error_code=None,
) -> Projection:
    return _p_text(
        text,
        role="error",
        title=title,
        error_kind="fatal",
        error_code=error_code,
    )


# ---------------------------------------------------------
# INTERNAL API
# ---------------------------------------------------------


def _p_text(
    text: str,
    *,
    role: Role = "info",
    title: str | None = None,
    error_kind: ErrorKind | None = None,
    error_code: str | None = None,
) -> Projection:
    return create_projection(
        role=role,
        title=title,
        error_kind=error_kind,
        error_code=error_code,
        blocks=[
            TextBlock(
                text=[InlineText("text", text)],
            )
        ],
    )
