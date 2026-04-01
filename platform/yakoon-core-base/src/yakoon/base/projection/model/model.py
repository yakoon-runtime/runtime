from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

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
    regions: dict[str, Any] = field(default_factory=dict)

    def with_body(self, blocks: list[Block]) -> Projection:
        return Projection(
            kind=self.kind,
            id=self.id,
            header=self.header,
            blocks=list(self.blocks),
            regions=self.regions,
        )

    def body_only(self, blocks: list[Block]) -> Projection:
        return Projection(
            kind=self.kind,
            id=self.id,
            header=None,
            blocks=list(blocks),
            regions=self.regions,
        )
