from dataclasses import dataclass, fields
from typing import Any


@dataclass
class NodeSpec:
    id: str
    type: str
    parent: str | None
    props: dict[str, Any]

    @classmethod
    def from_block(
        cls, block, *, parent: str, block_id: str | None = None
    ) -> "NodeSpec":

        block_id = block.id or block_id
        if block_id is None:
            raise RuntimeError("Block without id")

        props = {
            f.name: getattr(block, f.name)
            for f in fields(block)
            if f.name not in ("id", "type")
        }

        props["block"] = block

        return cls(
            id=block_id,
            type=block.type,
            parent=parent,
            props=props,
        )
