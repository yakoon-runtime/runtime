from y5n.base.document.schema import CHILDREN_FIELDS
from y5n.base.document.transfer import Node


def _extract_children(block: dict) -> list[dict]:
    field = CHILDREN_FIELDS.get(block.get("type", ""))
    return block.get(field, []) if field else []


def _build_node(block: dict, parent: str, depth: int) -> Node:
    block_id = block.get("id")
    if block_id is None:
        raise RuntimeError("Block without id")

    props = {k: v for k, v in block.items() if k not in ("id", "type")}

    return Node(
        id=block_id,
        type=block.get("type", ""),
        parent=parent,
        depth=depth,
        props=props,
    )


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
        self, block: dict, *, parent: str, depth: int
    ) -> tuple[Node, list[dict]]:
        node = _build_node(block, parent, depth)
        children = _extract_children(block)
        return node, children
