from yakoon.base.projection.model import Block
from yakoon.base.projection.transfer import Node


class EventTraversal:
    """
    Helper for Dispatcher.

    - NO recursion
    - NO iteration
    - ONLY block decomposition
    """

    ROOT_SUFFIX = ":root"

    def root_id(self, projection_id: str) -> str:
        return f"{projection_id}{self.ROOT_SUFFIX}"

    def resolve_parent(self, projection_id: str, parent_id: str | None) -> str:
        return parent_id or self.root_id(projection_id)

    def prepare_block(
        self, block: Block, *, parent: str, depth: int
    ) -> tuple[Node, list[Block]]:
        node = self._build_node(block, parent, depth)

        children = list(block.children())

        return node, children

    def _build_node(
        self,
        block: Block,
        parent: str,
        depth: int,
    ) -> Node:
        return Node.from_block(
            block,
            parent=parent,
            depth=depth,
        )
