from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from yakoon.base.projection import ProjectionHeader
from yakoon.base.projection.model import (
    Block,
    Inline,
    InlineText,
    Projection,
    TextBlock,
)

from ..nodes import ElementNode, Node, TextNode

BlockMapper = Callable[["Mapper", ElementNode], Block]
InlineMapper = Callable[["Mapper", ElementNode], Inline]


class Mapper:

    def __init__(self):
        self._block_mappers: dict[str, BlockMapper] = {}
        self._inline_mappers: dict[str, InlineMapper] = {}

    # -----------------
    # REGISTRATION
    # -----------------

    def register_block(self, tag: str, fn: BlockMapper) -> None:
        self._block_mappers[tag] = fn

    def register_inline(self, tag: str, fn: InlineMapper) -> None:
        self._inline_mappers[tag] = fn

    # -----------------
    # ENTRY
    # -----------------

    def map_projection(self, root: ElementNode) -> Projection:
        header = None
        projection_id = Projection.create_id()

        content_nodes: list[Node] = []

        for node in root.children:
            if is_whitespace(node):
                continue

            if is_element(node, "header"):
                if header is not None:
                    raise ValueError("Only one <header> allowed")

                assert isinstance(node, ElementNode)
                header = self._map_header(node)
                continue

            content_nodes.append(node)

        if header is None:
            header = self._default_header()

        blocks = self._map_nodes(content_nodes)
        blocks = assign_ids(projection_id, blocks)

        return Projection(
            kind="projection",
            id=projection_id,
            header=header,
            blocks=blocks,
        )

    # -----------------
    # HEADER
    # -----------------

    def _default_header(self) -> ProjectionHeader:
        return ProjectionHeader(
            role="info",
            title=None,
            subtitle=None,
            error_kind=None,
            meta=None,
        )

    def _map_header(self, node: ElementNode) -> ProjectionHeader:
        role = node.attrs.get("role", "info")

        if role not in ("info", "success", "warning", "error", "help"):
            raise ValueError(f"Invalid role: {role}")

        error_kind = node.attrs.get("error_kind")
        if error_kind not in (None, "validation", "system"):
            raise ValueError(f"Invalid error_kind: {error_kind}")

        return ProjectionHeader(
            role=role,
            title=node.attrs.get("title"),
            subtitle=node.attrs.get("subtitle"),
            error_kind=error_kind,
            meta=None,
        )

    # -----------------
    # NODES
    # -----------------

    def _map_nodes(self, nodes: list[Node]) -> list[Block]:
        blocks: list[Block] = []
        buffer: list[Node] = []

        for node in nodes:

            if isinstance(node, TextNode):
                if not node.text.strip():
                    continue

                buffer.append(node)
                continue

            if isinstance(node, ElementNode) and node.tag in self._inline_mappers:
                buffer.append(node)
                continue

            if buffer:
                blocks.append(self._flush_text(buffer))
                buffer = []

            assert isinstance(node, ElementNode)

            handler = self._block_mappers.get(node.tag)
            if not handler:
                raise ValueError(f"Unknown block tag: {node.tag}")

            blocks.append(handler(self, node))

        if buffer:
            blocks.append(self._flush_text(buffer))

        return blocks

    def _flush_text(self, nodes: list[Node]) -> TextBlock:
        inline = self._map_inline(nodes)
        return TextBlock(type="text", id=None, text=inline)

    # -----------------
    # INLINE
    # -----------------

    def _map_inline(self, nodes: list[Node]) -> list[Inline]:
        result: list[Inline] = []

        for node in nodes:

            if isinstance(node, TextNode):
                text = normalize_text(node.text)
                if text:
                    result.append(InlineText(text=text))
                continue

            assert isinstance(node, ElementNode)

            mapper = self._inline_mappers.get(node.tag)
            if not mapper:
                raise ValueError(f"Unknown inline tag: {node.tag}")

            result.append(mapper(self, node))

        return result


# -----------------
# UTILITIES
# -----------------


def is_element(node: Node, tag: str) -> bool:
    return isinstance(node, ElementNode) and node.tag == tag


def is_whitespace(node: Node) -> bool:
    return isinstance(node, TextNode) and not node.text.strip()


def normalize_text(text: str) -> str:
    return text  # .replace("\n", "")  # .lstrip("\n").rstrip()


def extract_text(node: Node) -> str:
    if isinstance(node, TextNode):
        return node.text
    if isinstance(node, ElementNode):
        return "".join(extract_text(c) for c in node.children)
    return ""


def assign_ids(projection_id: str, blocks: list[Block]) -> list[Block]:

    def assign(block: Block, path: str) -> Block:
        bid = block.id or path
        block = replace(block, id=bid)

        children = block.children()
        if not children:
            return block

        new_children = [assign(child, f"{bid}.{i}") for i, child in enumerate(children)]

        if hasattr(block, "blocks"):
            block = replace(block, blocks=new_children)

        elif hasattr(block, "items"):
            block = replace(block, items=new_children)

        return block

    return [assign(b, f"{projection_id}.{i}") for i, b in enumerate(blocks)]
