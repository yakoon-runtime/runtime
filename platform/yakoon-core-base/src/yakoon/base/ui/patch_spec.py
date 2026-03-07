from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .blocks import Block


@dataclass(frozen=True, slots=True)
class PatchReset:
    op: Literal["reset"] = "reset"


@dataclass(frozen=True, slots=True)
class PatchAppendBlock:
    op: Literal["append_block"] = "append_block"
    block: Block | None = None


@dataclass(frozen=True, slots=True)
class PatchAppendText:
    op: Literal["append_text"] = "append_text"
    block_id: str = ""
    text: str = ""


@dataclass(frozen=True, slots=True)
class PatchAppendChild:
    op: Literal["append_child"] = "append_child"
    block_id: str = ""
    parent_id: str = ""
    block: Block | None = None


PatchOp = PatchReset | PatchAppendBlock | PatchAppendText | PatchAppendChild


@dataclass(frozen=True, slots=True)
class PatchSpec:
    ops: list[PatchOp] = field(default_factory=list)
    final: bool = False
