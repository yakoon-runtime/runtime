from yakoon.base.ui import (
    Block,
    Node,
    PatchAppendStructure,
    PatchAppendText,
    PatchFinishNode,
    View,
)


class ViewTraversal:

    ROOT_SUFFIX = ":root"

    # ---------------------------------------------------------
    # Root
    # ---------------------------------------------------------

    def root_id(self, view_id: str) -> str:
        return f"{view_id}{self.ROOT_SUFFIX}"

    # ---------------------------------------------------------
    # Parent Resolution
    # ---------------------------------------------------------

    def resolve_parent(self, view_id: str, parent_id: str | None) -> str:
        if parent_id is not None:
            return parent_id
        return self.root_id(view_id)

    def prepare_block(self, block: Block, parent: str, depth: int):
        node = self.build_node(block, parent, depth)

        # bewusst eager → keine doppelte iteration
        children = list(block.children())
        text_fields = list(self.iter_text_fields(block))

        return node, children, text_fields

    def iter_ops(self, view: View):

        root = f"{view.id}{self.ROOT_SUFFIX}"

        for block in view.blocks:
            yield from self._iter_block(block, parent=root, depth=0)

    def _iter_block(self, block: Block, parent: str, depth: int):

        node = Node.from_block(
            block,
            parent=parent,
            depth=depth,
        )

        yield PatchAppendStructure(nodes=[node])

        # children zuerst (wie dein Streamer!)
        for child in block.children():
            yield from self._iter_block(child, node.id, depth + 1)

        # text fields (ungechunked!)
        for key in getattr(block, "__stream_fields__", ()):
            value = getattr(block, key)

            if isinstance(value, str) and value:
                yield PatchAppendText(
                    block_id=node.id,
                    key=key,
                    text=value,
                )

        yield PatchFinishNode(block_id=node.id)

    def build_node(self, block: Block, parent: str, depth: int) -> Node:
        return Node.from_block(
            block,
            parent=parent,
            depth=depth,
        )

    def iter_text_fields(self, block: Block):
        for key in getattr(block, "__stream_fields__", ()):
            value = getattr(block, key)
            if isinstance(value, str) and value:
                yield key, value
