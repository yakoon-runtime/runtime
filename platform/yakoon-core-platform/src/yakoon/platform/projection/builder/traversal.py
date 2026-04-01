from yakoon.base.projection.model import Block
from yakoon.base.projection.transport import Node


class ViewTraversal:
    """
    Helper for Dispatcher.

    - NO recursion
    - NO iteration
    - ONLY block decomposition
    """

    ROOT_SUFFIX = ":root"

    # ---------------------------------------------------------
    # Root / Parent
    # ---------------------------------------------------------

    def root_id(self, projection_id: str) -> str:
        return f"{projection_id}{self.ROOT_SUFFIX}"

    def resolve_parent(self, projection_id: str, parent_id: str | None) -> str:
        return parent_id or self.root_id(projection_id)

    # ---------------------------------------------------------
    # Block decomposition (zentrale Funktion)
    # ---------------------------------------------------------

    def prepare_block(
        self, block: Block, *, parent: str, depth: int, region: str | None
    ):
        node = self.build_node(block, parent, depth, region)

        # eager extraction (keine doppelte iteration!)
        children = list(block.children())
        text_fields = list(self.iter_text_fields(block))

        return node, children, text_fields

    # ---------------------------------------------------------

    def build_node(
        self,
        block: Block,
        parent: str,
        depth: int,
        region: str | None,
    ) -> Node:
        return Node.from_block(
            block,
            parent=parent,
            depth=depth,
            region=region,
        )

    # ---------------------------------------------------------

    def iter_text_fields(self, block: Block):
        for key in getattr(block, "__stream_fields__", ()):
            value = getattr(block, key)
            if isinstance(value, str) and value:
                yield key, value
