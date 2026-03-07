from __future__ import annotations

from .blocks import TextBlock
from .output_spec import OutputSpec
from .view_spec import ViewSpec


def v_text(
    text: str,
    *,
    role: str = "info",
    error_kind: str | None = None,
    title: str | None = None,
    mode: str = "replace",
) -> ViewSpec:
    return ViewSpec(
        kind="view",
        mode=mode,
        id=None,
        output=OutputSpec(
            kind="message",
            role=role,
            error_kind=error_kind,
            title=title,
            blocks=[TextBlock(type="text", text=text)],
            meta=None,
        ),
        input=None,
        meta=None,
    )


def v_error(
    text: str, *, error_kind: str | None = "system", title: str | None = None
) -> ViewSpec:
    return v_text(text, error_kind=error_kind, role="error", title=title)


def v_info(text: str, *, title: str | None = None) -> ViewSpec:
    return v_text(text, role="info", title=title)
