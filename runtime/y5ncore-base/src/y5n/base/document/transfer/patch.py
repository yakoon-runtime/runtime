from dataclasses import dataclass, field
from typing import Literal

from .node import Node


@dataclass(frozen=True, slots=True)
class PatchReset:
    op: Literal["reset"] = "reset"


@dataclass(frozen=True, slots=True)
class PatchAppendStructure:
    op: Literal["append_structure"] = "append_structure"
    nodes: list[Node] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PatchFinishNode:
    block_id: str
    op: Literal["finish_node"] = "finish_node"


PatchOp = PatchReset | PatchAppendStructure | PatchFinishNode


@dataclass(frozen=True, slots=True)
class Patch:
    ops: list[PatchOp] = field(default_factory=list)
    final: bool = False

    def has_reset(self) -> bool:
        return any(isinstance(op, PatchReset) for op in self.ops)
