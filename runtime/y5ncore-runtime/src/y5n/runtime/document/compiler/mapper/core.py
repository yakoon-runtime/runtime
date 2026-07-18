from __future__ import annotations

from collections.abc import Callable, Mapping

from y5n.base.document.model import (
    Block,
    Inline,
    InlineText,
)

from ..nodes import ElementNode, Node, TextNode
from .resolver import BlockResolver

BlockMapper = Callable[["Mapper", ElementNode], Block]
InlineMapper = Callable[["Mapper", ElementNode], Inline]


class Mapper:

    def __init__(self, resolvers: Mapping[type, BlockResolver]):
        self._block_mappers: dict[str, BlockMapper] = {}
        self._inline_mappers: dict[str, InlineMapper] = {}
        self._resolvers = resolvers

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

    def map_document(self, root: ElementNode) -> dict:
        header = None

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

        return _blocks_to_dict(header, blocks)

    # -----------------
    # HEADER
    # -----------------

    def _default_header(self) -> dict:
        return {
            "role": "info",
        }

    def _map_header(self, node: ElementNode) -> dict:
        role = node.attrs.get("role", "info")

        if role not in ("info", "success", "warning", "error", "help"):
            raise ValueError(f"Invalid role: {role}")

        error_kind = node.attrs.get("error_kind")
        if error_kind not in (None, "validation", "system"):
            raise ValueError(f"Invalid error_kind: {error_kind}")

        return {
            "role": role,
            "title": node.attrs.get("title"),
            "subtitle": node.attrs.get("subtitle"),
            "error_kind": error_kind,
        }

    # -----------------
    # NODES
    # -----------------

    def _map_nodes(self, nodes: list[Node]) -> list[dict]:
        blocks: list[dict] = []
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

            block = handler(self, node)

            if self._resolvers:
                resolver = self._resolvers.get(type(block))
                if resolver:
                    block = resolver.resolve(block)

            blocks.append(_block_to_dict(block))

        if buffer:
            blocks.append(self._flush_text(buffer))

        return blocks

    def _flush_text(self, nodes: list[Node]) -> dict:
        inline = self._map_inline(nodes)
        return {"type": "text", "text": [_inline_to_dict(v) for v in inline]}

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

        if result and isinstance(result[0], InlineText):
            result[0] = InlineText(text=result[0].text.lstrip())
        if result and isinstance(result[-1], InlineText):
            result[-1] = InlineText(text=result[-1].text.rstrip())

        return result


# -----------------
# INLINE → DICT
# -----------------


def _inline_to_dict(inline: Inline) -> dict:
    from dataclasses import asdict

    return asdict(inline)


# -----------------
# BLOCK → DICT
# -----------------


def _block_to_dict(block: Block) -> dict:
    from dataclasses import fields

    data = {}
    for f in fields(block):
        if f.name in ("id", "type"):
            if f.name == "type":
                data[f.name] = getattr(block, f.name)
            continue
        val = getattr(block, f.name)
        if isinstance(val, (list, tuple)):
            data[f.name] = [_to_json_safe(v) for v in val]
        else:
            data[f.name] = _to_json_safe(val)
    data["id"] = None
    return data


def _to_json_safe(val):
    from dataclasses import asdict

    if hasattr(val, "__dataclass_fields__"):
        return asdict(val)
    return val


def _blocks_to_dict(header: dict, blocks: list[dict]) -> dict:
    return {
        "kind": "document",
        "header": header,
        "blocks": blocks,
    }


# -----------------
# UTILITIES
# -----------------


def is_element(node: Node, tag: str) -> bool:
    return isinstance(node, ElementNode) and node.tag == tag


def is_whitespace(node: Node) -> bool:
    return isinstance(node, TextNode) and not node.text.strip()


def normalize_text(text: str) -> str:
    return text


def extract_text(node: Node) -> str:
    if isinstance(node, TextNode):
        return node.text
    if isinstance(node, ElementNode):
        return "".join(extract_text(c) for c in node.children)
    return ""
