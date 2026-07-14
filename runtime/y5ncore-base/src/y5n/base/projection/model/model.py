from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from typing import Literal

from .block import Block, TextBlock
from .header import ProjectionHeader


@dataclass(frozen=True, slots=True)
class Projection:
    """
    Canonical UI document.

    A view is one structured document:
      - header: document-level framing
      - blocks: document body
    """

    id: str
    kind: Literal["projection"] = "projection"
    header: ProjectionHeader | None = None

    blocks: list[Block] = field(default_factory=list)

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
            header=header or ProjectionHeader(),
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

            replaced = replace(block, id=block_id)

            children = list(replaced.children())
            if children:
                assigned = Projection._assign_block_ids(block_id, children)
                if hasattr(replaced, "items"):
                    replaced = replace(replaced, items=assigned)
                else:
                    replaced = replace(replaced, blocks=assigned)

            result.append(replaced)

        return result

    @staticmethod
    def create_id() -> str:
        return f"prj.{uuid.uuid4().hex}"

    def with_body(self, blocks: list[Block]) -> Projection:
        return Projection(
            kind=self.kind,
            id=self.id,
            header=self.header,
            blocks=list(blocks),
        )

    def body_only(self, blocks: list[Block]) -> Projection:
        return Projection(
            kind=self.kind,
            id=self.id,
            header=None,
            blocks=list(blocks),
        )


# ----------------------------------
# HELPER
# ----------------------------------


def to_text(text: str) -> Projection:
    return Projection.create(
        blocks=[
            TextBlock.create(text=text),
        ] if text else []
    )
