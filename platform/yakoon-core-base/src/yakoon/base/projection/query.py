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

    - blocks  = primary structure
    - regions = derived grouping (by node.region)
    """

    def __init__(self, *, include_text: bool = False):
        self.include_text = include_text

        self.header = None

        #  primary structure
        self.regions: dict[str | None, list[Block]] = {}

        # compatibility (flattened)
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

        q.header = projection.header

        for block in projection.blocks:
            q._append_block(
                block,
                region=getattr(block, "region", None),
            )

        return q

    # ---------------------------------------------------------
    # INTERNAL BUILDING
    # ---------------------------------------------------------

    def _append_block(self, block: Block, *, region: str | None = None):
        self.blocks.append(block)

        # regional (truth)
        if region not in self.regions:
            self.regions[region] = []

        self.regions[region].append(block)

        # field indexing
        for field in getattr(block, "fields", []):
            self._fields.append(field)

            if getattr(field, "required", False):
                self._required_fields.append(field)

    # ---------------------------------------------------------
    # APPLY (Streaming Mode)
    # ---------------------------------------------------------

    def apply(self, event: ProjectionEvent):

        for op in event.patch.ops:

            # RESET
            if isinstance(op, PatchReset):
                self.header = None
                self.blocks.clear()
                self.regions.clear()
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

                    region = getattr(node, "region", None)

                    self._append_block(block, region=region)

            # TEXT
            elif isinstance(op, PatchAppendText):

                if self._text is None:
                    continue

                key = (op.block_id, op.key)
                self._text[key] = self._text.get(key, "") + op.text

        # HEADER
        if event.header:
            self.header = event.header

    # ---------------------------------------------------------
    # STATE
    # ---------------------------------------------------------

    def expects_input(self) -> bool:
        return bool(self._fields)

    def has_blocks(self) -> bool:
        return bool(self.blocks)

    def has_regions(self) -> bool:
        return bool(self.regions)

    def has_fields(self) -> bool:
        return bool(self._fields)

    # ---------------------------------------------------------
    # FIELD QUERIES
    # ---------------------------------------------------------

    def fields(self) -> list[Field]:
        return self._fields

    def bound_fields(self) -> list[Field]:
        return [f for f in self._fields if getattr(f, "var", None)]

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
    # REGION QUERIES
    # ---------------------------------------------------------

    def get_regions(self) -> dict[str | None, list[Block]]:
        return self.regions

    def get_region(self, name: str) -> list[Block]:
        return self.regions.get(name, [])

    def has_region(self, name: str) -> bool:
        return name in self.regions

    # ---------------------------------------------------------
    # TEXT (optional)
    # ---------------------------------------------------------

    def get_text(self, block_id: str, key: str) -> str:
        if self._text is None:
            raise RuntimeError("Text not enabled in ProjectionQuery")

        return self._text.get((block_id, key), "")
