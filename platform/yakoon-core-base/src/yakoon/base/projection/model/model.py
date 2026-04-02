from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
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

    @classmethod
    def create(
        cls,
        *,
        blocks: list[Block],
        header: ProjectionHeader | None = None,
        id: str | None = None,
    ) -> Projection:

        pid = id or cls.create_id()
        blocks_with_ids = cls._assign_block_ids(pid, blocks)

        return cls(
            id=pid,
            header=header,
            blocks=blocks_with_ids,
        )

    @staticmethod
    def _assign_block_ids(pid: str, blocks: list[Block]) -> list[Block]:
        result = []

        for i, block in enumerate(blocks):
            if block.id is None:
                block_id = f"{pid}:b{i}"
            else:
                block_id = block.id

            result.append(replace(block, id=block_id))  # dataclass replace

        return result

    @staticmethod
    def create_id() -> str:
        return f"prj.{uuid.uuid4().hex}"

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
