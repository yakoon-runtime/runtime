from __future__ import annotations

from yakoon.base.ui import Block

from .event import ViewEvent


class ViewDocument:

    def __init__(self):
        self.header = None
        self.blocks: list[Block] = []

    # ------------------------
    # Patch anwenden
    # ------------------------

    def apply(self, event: ViewEvent):

        if event.header:
            self.header = event.header

        patch = event.patch

        for op in patch.ops:
            if op is None:
                raise RuntimeError("")
            if op.op == "reset":
                self.blocks = []

            elif op.op == "append_structure":
                for node in op.nodes:
                    block = node.props.get("block")
                    if block:
                        self.blocks.append(block)

    # ----------------------------------------
    # PUBLIC
    # ----------------------------------------

    def expects_input(self):
        return self.header and self.header.expects_input

    def has_fields(self):
        return len(self.get_fields()) > 0

    def get_first_field(self):
        fields = self.get_fields()
        return fields[0] if fields else None

    # ----------------------------------------
    # QUERIES
    # ----------------------------------------

    def get_blocks(self):
        return self.blocks

    def get_fields(self):
        fields = []
        for block in self.blocks:
            for field in getattr(block, "fields", []):
                fields.append(field)

        return fields

    def get_blocks_by_type(self, type_name):
        return [b for b in self.blocks if getattr(b, "type", None) == type_name]

    def get_required_fields(self):
        result = []
        for block in self.blocks:
            for field in getattr(block, "fields", []):
                if getattr(field, "required", False):
                    result.append(field)

        return result
