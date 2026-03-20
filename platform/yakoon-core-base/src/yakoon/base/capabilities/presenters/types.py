from dataclasses import dataclass

from yakoon.base.ui.blocks import Block


@dataclass
class BlockGroup:
    id: str
    type: str
    blocks: list[Block]
