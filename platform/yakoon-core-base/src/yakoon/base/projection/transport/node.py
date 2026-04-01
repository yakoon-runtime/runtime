from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any


@dataclass(slots=True)
class Node:
    """
    Transport node representing a block in the projection stream.

    Structure:
    - id / parent / depth → tree structure
    - region              → layout grouping (orthogonal!)
    - props               → block payload
    """

    id: str
    type: str
    parent: str | None
    depth: int

    # layout dimension
    region: str | None = None

    # payload
    props: dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Factory
    # ---------------------------------------------------------

    @classmethod
    def from_block(
        cls,
        block,
        *,
        parent: str | None,
        depth: int,
        region: str | None,
        block_id: str | None = None,
    ) -> Node:

        block_id = block.id or block_id
        if block_id is None:
            raise RuntimeError("Block without id")

        props = {
            f.name: getattr(block, f.name)
            for f in fields(block)
            if f.name not in ("id", "type")
        }

        # original block (for Query / reconstruction)
        props["block"] = block

        return cls(
            id=block_id,
            type=block.type,
            parent=parent,
            depth=depth,
            region=region,
            props=props,
        )
