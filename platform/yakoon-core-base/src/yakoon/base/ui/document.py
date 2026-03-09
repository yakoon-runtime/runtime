from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .blocks import Block

Role = Literal["info", "success", "warning", "error", "help"]
ErrorKind = Literal["validation", "system"] | None


@dataclass(frozen=True, slots=True)
class ViewUI:
    secret: bool = False
    # später z.B. focus, disabled, placeholder, collapsed, ...


@dataclass(frozen=True, slots=True)
class ViewMeta:
    ui: ViewUI | None = None


@dataclass(frozen=True, slots=True)
class ViewSpec:
    """
    Canonical UI document.

    A view is one structured UI document that may contain:
      - display blocks
      - interactive blocks

    Transport and incremental updates happen via PatchSpec.
    """

    kind: Literal["view"] = "view"
    id: str | None = None

    role: Role | None = "info"
    title: str | None = None
    subtitle: str | None = None
    blocks: list[Block] = field(default_factory=list)

    error_kind: ErrorKind = None
    meta: dict[str, Any] | ViewMeta | None = None
