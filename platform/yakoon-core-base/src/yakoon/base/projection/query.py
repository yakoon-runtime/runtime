from __future__ import annotations

from .model import Block, Field, Projection
from .transport import (
    PatchAppendStructure,
    PatchAppendText,
    PatchReset,
    ProjectionEvent,
)


class ProjectionQuery:
    """
    Unified query model for Projection.

    - blocks = flat list
    """

    def __init__(self, *, include_text: bool = False):
        self.include_text = include_text

        self.header = None
        self._projection: Projection | None = None

        # flat
        self.blocks: list[Block] = []

        # indexed
        self._fields: list[Field] = []
        self._required_fields: list[Field] = []

        # optional text buffer
        self._text: dict[tuple[str, str], str] | None = {} if include_text else None

    # ---------------------------------------------------------
    # FACTORIES
    # ---------------------------------------------------------

    @classmethod
    def from_projection(
        cls, projection: Projection, *, include_text: bool = False
    ) -> ProjectionQuery:
        q = cls(include_text=include_text)

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
        self.blocks.append(block)

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

            # RESET
            if isinstance(op, PatchReset):
                self.header = None
                self.blocks.clear()
                self._fields.clear()
                self._required_fields.clear()

                if self._text is not None:
                    self._text.clear()

            # STRUCTURE
            elif isinstance(op, PatchAppendStructure):

                for node in op.nodes:
                    block = node.props.get("block")
                    if not block:
                        continue

                    self._append_block(block)

            # TEXT
            elif isinstance(op, PatchAppendText):

                if self._text is None:
                    continue

                key = (op.block_id, op.key)
                self._text[key] = self._text.get(key, "") + op.text

        # HEADER UPDATE
        if event.header:
            self.header = event.header

    # ---------------------------------------------------------
    # STATE
    # ---------------------------------------------------------

    def expects_input(self) -> bool:
        return bool(self._fields)

    def has_blocks(self) -> bool:
        return bool(self.blocks)

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
        return self.blocks

    def get_blocks_by_type(self, type_name: str) -> list[Block]:
        return [b for b in self.blocks if getattr(b, "type", None) == type_name]

    # ---------------------------------------------------------
    # TEXT (optional)
    # ---------------------------------------------------------

    def get_text(self, block_id: str, key: str) -> str:
        if self._text is None:
            raise RuntimeError("Text not enabled in ProjectionQuery")

        return self._text.get((block_id, key), "")
