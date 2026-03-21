from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from yakoon.base.ui import Block, Field, View, ViewHeader


@dataclass
class BlockGroup:
    id: str
    type: str
    blocks: list[Block]


class PresenterView(Protocol):

    @property
    def id(self) -> str: ...
    @property
    def header(self) -> ViewHeader | None: ...

    def blocks(self) -> list[Block]: ...
    def raw(self) -> View: ...
    def expects_input(self) -> bool: ...
    def has_blocks(self) -> bool: ...

    # --------------------------------------------------------
    # Field Queries
    # --------------------------------------------------------

    def fields(self) -> list[Field]: ...
    def has_fields(self) -> bool: ...
    def first_field(self) -> Field | None: ...
    def required_fields(self) -> list[Field]: ...

    # --------------------------------------------------------
    # Block Queries
    # --------------------------------------------------------

    def blocks_by_type(self, type_name: str) -> list[Block]: ...

    # --------------------------------------------------------
    # Grouping (für Compiler)
    # --------------------------------------------------------

    def groups(self) -> list[BlockGroup]: ...

    # --------------------------------------------------------
    # Transformations
    # --------------------------------------------------------

    def subview(self, blocks: list) -> PresenterView: ...
    def body_only(self, blocks: list) -> PresenterView: ...
