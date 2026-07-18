from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from typing import Literal

from .block import Block
from .header import DocumentHeader


@dataclass(frozen=True, slots=True)
class Document:
    """
    Canonical UI document.

    A view is one structured document:
      - header: document-level framing
      - blocks: document body
    """

    id: str
    kind: Literal["document"] = "document"
    header: DocumentHeader | None = None

    blocks: list[Block] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        blocks: list[Block],
        header: DocumentHeader | None = None,
        id: str | None = None,
    ) -> Document:

        pid = id or cls.create_id()
        blocks_with_ids = cls._assign_block_ids(pid, blocks)

        return cls(
            id=pid,
            header=header or DocumentHeader(),
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
                assigned = Document._assign_block_ids(block_id, children)
                if hasattr(replaced, "items"):
                    replaced = replace(replaced, items=assigned)
                else:
                    replaced = replace(replaced, blocks=assigned)

            result.append(replaced)

        return result

    @staticmethod
    def create_id() -> str:
        return f"doc.{uuid.uuid4().hex}"

    def with_body(self, blocks: list[Block]) -> Document:
        return Document(
            kind=self.kind,
            id=self.id,
            header=self.header,
            blocks=list(blocks),
        )

    def body_only(self, blocks: list[Block]) -> Document:
        return Document(
            kind=self.kind,
            id=self.id,
            header=None,
            blocks=list(blocks),
        )


# ----------------------------------
# HELPER
# ----------------------------------


def to_text(text: str) -> dict:
    if not text:
        return {"kind": "document", "header": {"role": "info"}, "blocks": []}
    return {
        "kind": "document",
        "header": {"role": "info"},
        "blocks": [
            {
                "type": "text",
                "text": [{"type": "text", "text": text}],
            }
        ],
    }
