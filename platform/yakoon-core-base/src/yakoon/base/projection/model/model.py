from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .block import Block
from .header import ProjectionHeader


@dataclass(frozen=True, slots=True)
class Projection:
    """
    Canonical UI document.

    A view is one structured document:
      - header: document-level framing
      - blocks: document body
    """

    kind: Literal["projection"] = "projection"
    id: str | None = None
    header: ProjectionHeader | None = None
    blocks: list[Block] = field(default_factory=list)

    def with_body(self, blocks: list[Block]) -> Projection:
        return Projection(
            kind=self.kind,
            id=self.id,
            header=self.header,
            blocks=blocks,
        )

    def body_only(self, blocks: list[Block]) -> Projection:
        return Projection(
            kind=self.kind,
            id=self.id,
            header=None,
            blocks=blocks,
        )
