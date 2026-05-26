from __future__ import annotations

from .model import Block, Field, Projection
from .transfer import (
    PatchAppendStructure,
    PatchReset,
    ProjectionEvent,
)


class ProjectionQuery:
    """
    Unified query model for Projection.

    - blocks = flat list
    """

    def __init__(self):

        self.header = None
        self._projection: Projection | None = None

        # flat
        self._blocks: list[Block] = []

        # indexed
        self._fields: list[Field] = []
        self._required_fields: list[Field] = []

    # ---------------------------------------------------------
    # FACTORIES
    # ---------------------------------------------------------

    @classmethod
    def from_projection(cls, projection: Projection) -> ProjectionQuery:

        q = cls()
        q._projection = projection
        q.header = projection.header

        # ---------------------------------------------------------
        # Blocks EINORDNEN
        # ---------------------------------------------------------
        for block in projection.blocks:
            q._append_block(block)

        return q

    # ---------------------------------------------------------
    # INTERNAL
    # ---------------------------------------------------------

    def _append_block(self, block: Block):
        self._blocks.append(block)

        projection = self._projection
        if projection is None:
            return

        # field indexing
        for field in getattr(block, "fields", []):
            self._fields.append(field)

            if getattr(field, "required", False):
                self._required_fields.append(field)

    # ---------------------------------------------------------
    # APPLY (Streaming)
    # ---------------------------------------------------------

    def apply(self, event: ProjectionEvent):

        for op in event.patch.ops:

            if isinstance(op, PatchReset):
                self.header = None
                self._blocks.clear()
                self._fields.clear()
                self._required_fields.clear()

            elif isinstance(op, PatchAppendStructure):

                for node in op.nodes:
                    block = node.props.get("block")
                    if not block:
                        continue

                    self._append_block(block)

        if event.header:
            self.header = event.header

    # ---------------------------------------------------------
    # STATE
    # ---------------------------------------------------------

    def expects_input(self) -> bool:
        return bool(self._fields)

    def has_blocks(self) -> bool:
        return bool(self._blocks)

    def has_fields(self) -> bool:
        return bool(self._fields)

    # ---------------------------------------------------------
    # FIELD QUERIES
    # ---------------------------------------------------------

    def fields(self) -> list[Field]:
        return self._fields

    def required_fields(self) -> list[Field]:
        return self._required_fields

    def first_field(self) -> Field | None:
        return self._fields[0] if self._fields else None

    # ---------------------------------------------------------
    # BLOCK QUERIES
    # ---------------------------------------------------------

    def get_blocks(self) -> list[Block]:
        return self._blocks

    def get_blocks_by_type(self, type_name: str) -> list[Block]:
        return [b for b in self._blocks if getattr(b, "type", None) == type_name]
