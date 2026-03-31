from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .block import Block

Role = Literal["info", "success", "warning", "error", "help"]
ErrorKind = Literal[
    "validation",  # Field / Input
    "domain",  # Business / erwartbar
    "system",  # Infrastruktur
    "fatal",  # Crash / unrecoverable
]


@dataclass(frozen=True, slots=True)
class ViewUI:
    secret: bool = False


@dataclass(frozen=True, slots=True)
class ViewMeta:
    ui: ViewUI | None = None


@dataclass(frozen=True, slots=True)
class ViewHeader:
    """
    Document-level presentation metadata.

    This is the stable header that hosts may render as:
      - title / subtitle
      - role-based framing / icon / color
      - future document-level presentation hints
    """

    role: Role | None = "info"
    title: str | None = None
    subtitle: str | None = None
    error_kind: ErrorKind | None = None
    error_code: str | None = None
    meta: dict[str, Any] | ViewMeta | None = None
    expects_input: bool = False


@dataclass(frozen=True, slots=True)
class View:
    """
    Canonical UI document.

    A view is one structured document:
      - header: document-level framing
      - blocks: document body
    """

    kind: Literal["view"] = "view"
    id: str | None = None
    header: ViewHeader | None = None
    blocks: list[Block] = field(default_factory=list)

    def with_body(self, blocks: list[Block]) -> View:
        return View(
            kind=self.kind,
            id=self.id,
            header=self.header,
            blocks=blocks,
        )

    def body_only(self, blocks: list[Block]) -> View:
        return View(
            kind=self.kind,
            id=self.id,
            header=None,
            blocks=blocks,
        )
