from __future__ import annotations

from .block import Block
from .event import ViewEvent
from .patch import PatchAppendStructure, PatchAppendText, PatchReset


class ViewQuery:

    def __init__(self, *, include_text: bool = False):
        self.include_text = include_text

        self.header = None

        # primary
        self.blocks: list[Block] = []

        # indexed
        self._fields = []
        self._required_fields = []

        # optional
        self._text: dict[tuple[str, str], str] | None = {} if include_text else None

    # ---------------------------------------------------------
    # APPLY
    # ---------------------------------------------------------

    def apply(self, event: ViewEvent):

        for op in event.patch.ops:

            # -------------------------
            # RESET
            # -------------------------
            if isinstance(op, PatchReset):
                self.header = None
                self.blocks.clear()
                self._fields.clear()
                self._required_fields.clear()

                if self._text is not None:
                    self._text.clear()

            # -------------------------
            # STRUCTURE
            # -------------------------
            elif isinstance(op, PatchAppendStructure):

                for node in op.nodes:
                    block = node.props.get("block")
                    if not block:
                        continue

                    self.blocks.append(block)

                    # Index direkt aufbauen
                    for field in getattr(block, "fields", []):
                        self._fields.append(field)

                        if getattr(field, "required", False):
                            self._required_fields.append(field)

            # -------------------------
            # TEXT (optional)
            # -------------------------
            elif isinstance(op, PatchAppendText):

                if self._text is None:
                    continue

                key = (op.block_id, op.key)
                self._text[key] = self._text.get(key, "") + op.text

        # -------------------------
        # HEADER
        # -------------------------

        if event.header:
            self.header = event.header

    # ---------------------------------------------------------
    # PUBLIC
    # ---------------------------------------------------------

    def expects_input(self) -> bool:
        return bool(self.header and self.header.expects_input)

    def has_fields(self) -> bool:
        return bool(self._fields)

    def get_first_field(self):
        return self._fields[0] if self._fields else None

    # ---------------------------------------------------------
    # QUERIES (O(1))
    # ---------------------------------------------------------

    def get_blocks(self):
        return self.blocks

    def get_fields(self):
        return self._fields

    def get_required_fields(self):
        return self._required_fields

    def get_blocks_by_type(self, type_name):
        return [b for b in self.blocks if getattr(b, "type", None) == type_name]

    def get_text(self, block_id: str, key: str) -> str:
        if self._text is None:
            raise RuntimeError("Text not enabled in ViewQuery")

        return self._text.get((block_id, key), "")
