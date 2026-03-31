from __future__ import annotations

from yakoon.base.capabilities.presenters import BlockGroup
from yakoon.base.projection import View
from yakoon.base.projection.block import Block
from yakoon.base.projection.field import Field
from yakoon.base.projection.view import ViewHeader


class DefaultPresenterView:

    def __init__(self, spec: View):
        if spec.id is None:
            raise RuntimeError("View without id")

        self._spec = spec

    # --------------------------------------------------------
    # Core Access
    # --------------------------------------------------------

    @property
    def id(self) -> str:
        return self._spec.id  # type: ignore

    @property
    def header(self) -> ViewHeader | None:
        return self._spec.header

    @property
    def view(self) -> View:
        return self._spec

    def blocks(self) -> list[Block]:
        return self._spec.blocks

    # --------------------------------------------------------
    # Document State
    # --------------------------------------------------------

    def expects_input(self) -> bool:
        return bool(self.header and self.header.expects_input)

    def has_blocks(self) -> bool:
        return bool(self._spec.blocks)

    # --------------------------------------------------------
    # Field Queries
    # --------------------------------------------------------

    def fields(self) -> list[Field]:
        result = []

        for block in self._spec.blocks:
            for field in getattr(block, "fields", []):
                result.append(field)

        return result

    def has_fields(self) -> bool:
        return bool(self.fields())

    def first_field(self) -> Field | None:
        f = self.fields()
        return f[0] if f else None

    def required_fields(self) -> list[Field]:
        result: list[Field] = []

        for field in self.fields():
            if getattr(field, "required", False):
                result.append(field)

        return result

    # --------------------------------------------------------
    # Block Queries
    # --------------------------------------------------------

    def blocks_by_type(self, type_name: str) -> list[Block]:
        return [b for b in self._spec.blocks if getattr(b, "type", None) == type_name]

    # --------------------------------------------------------
    # Grouping (für Compiler)
    # --------------------------------------------------------

    def groups(self) -> list[BlockGroup]:
        """
        Gruppiert Blöcke nach semantischem Verhalten
        (nicht rein nach type!)
        """

        groups: list[BlockGroup] = []

        current_blocks = []
        current_type = None

        for block in self._spec.blocks:

            block_type = block.type

            if current_type is None:
                current_type = block_type

            if block_type != current_type:
                groups.append(BlockGroup(self.id, current_type, current_blocks))
                current_type = block_type
                current_blocks = []

            current_blocks.append(block)

        if current_blocks:
            groups.append(BlockGroup(self.id, current_type, current_blocks))  # type: ignore

        return groups

    # --------------------------------------------------------
    # Transformations
    # --------------------------------------------------------

    def subview(self, blocks: list) -> DefaultPresenterView:
        return DefaultPresenterView(self._spec.with_body(blocks))

    def body_only(self, blocks: list) -> DefaultPresenterView:
        return DefaultPresenterView(self._spec.body_only(blocks))
