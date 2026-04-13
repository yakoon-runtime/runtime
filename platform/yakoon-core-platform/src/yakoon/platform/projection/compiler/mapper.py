from __future__ import annotations

from dataclasses import replace

from yakoon.base.projection import ProjectionHeader
from yakoon.base.projection.model import (
    Action,
    ActionBlock,
    Block,
    FieldsBlock,
    Inline,
    InlineText,
    KvBlock,
    KvItemBlock,
    ListBlock,
    ListItemBlock,
    Projection,
    RuleBlock,
    SpacerBlock,
    TextBlock,
)
from yakoon.base.projection.model.field import Field
from yakoon.base.projection.model.inline import (
    InlineCmd,
    InlineCode,
    InlineLink,
    InlineSelect,
)

from .nodes import ElementNode, Node, TextNode


class Mapper:

    def __init__(self):

        self._block_mappers = {
            "kv": self._map_kv,
            "list": self._map_list,
            "rule": self._map_rule,
            "spacer": self._map_spacer,
            "actions": self._map_actions,
            "fields": self._map_fields,
        }
        self._inline_mappers = {
            "cmd": self._map_inline_cmd,
            "code": self._map_inline_code,
            "link": self._map_inline_link,
            "select": self._map_inline_select,
        }

    def map_projection(self, root: ElementNode) -> Projection:
        header = None

        projection_id = Projection.create_id()

        # -------- HEADER EXTRAHIEREN --------
        content_nodes: list[Node] = []

        for node in root.children:
            if is_whitespace(node):
                continue

            if is_element(node, "header"):
                if header is not None:
                    raise ValueError("Only one <header> allowed")

                header = self._map_header(node)  # type: ignore
                continue

            content_nodes.append(node)

        if header is None:
            header = self._default_header()

        # -------- BLOCKS MAPPEN --------
        blocks = self._map_nodes(content_nodes)

        # -------- IDS --------
        blocks = assign_ids(projection_id, blocks)

        return Projection(
            kind="projection",
            id=projection_id,
            header=header,
            blocks=blocks,
        )

    # --------------
    # HEADER
    # --------------

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

    # --------------
    # NODES
    # --------------

    def _map_nodes(self, nodes: list[Node]) -> list[Block]:
        blocks: list[Block] = []
        buffer: list[Node] = []

        for node in nodes:

            # -------- TEXT --------
            if isinstance(node, TextNode):
                buffer.append(node)
                continue

            # -------- INLINE --------
            if isinstance(node, ElementNode) and node.tag in self._inline_mappers:
                buffer.append(node)
                continue

            # -------- BLOCK --------
            if buffer:
                blocks.append(self._flush_text(buffer))
                buffer = []

            assert isinstance(node, ElementNode)

            handler = self._block_mappers.get(node.tag)
            if not handler:
                raise ValueError(f"Unknown block tag: {node.tag}")

            blocks.append(handler(node))

        # -------- REST --------
        if buffer:
            blocks.append(self._flush_text(buffer))

        return blocks

    def _flush_text(self, nodes: list[Node]) -> TextBlock:
        inline = self._map_inline(nodes)
        return TextBlock(type="text", id=None, text=inline)

    # --------------
    # MAP BLOCKS
    # --------------

    def _map_list(self, node: ElementNode) -> ListBlock:
        items: list[ListItemBlock] = []

        for child in node.children:
            if is_whitespace(child):
                continue

            if not is_element(child, "item"):
                raise ValueError("<list> can only contain <item>")

            items.append(self._map_list_item(child))  # type: ignore

        return ListBlock(
            type="list",
            id=None,
            items=items,
        )

    def _map_list_item(self, node: ElementNode) -> ListItemBlock:

        inline = self._map_inline(node.children)

        return ListItemBlock(
            type="list_item",
            id=None,
            text=inline,
            blocks=None,
        )

    def _map_rule(self, node: ElementNode) -> RuleBlock:
        style = node.attrs.get("style", "normal")

        if style not in ("subtle", "normal", "strong"):
            raise ValueError(
                f"Invalid rule style: {style!r}. Expected one of ('subtle','normal','strong')"
            )

        return RuleBlock(
            type="rule",
            id=None,
            style=style,
        )

    def _map_spacer(self, node: ElementNode) -> SpacerBlock:
        raw = node.attrs.get("size", "1")

        try:
            size = int(raw)
        except ValueError as e:
            raise ValueError(f"Spacer size must be an integer, got {raw!r}") from e

        if size < 0:
            raise ValueError("Spacer size must be >= 0")

        return SpacerBlock(
            type="spacer",
            id=None,
            size=size,
        )

    def _map_kv(self, node: ElementNode) -> KvBlock:
        items: list[KvItemBlock] = []

        for child in node.children:
            if is_whitespace(child):
                continue

            if not is_element(child, "item"):
                raise ValueError("<kv> can only contain <item>")

            assert isinstance(child, ElementNode)
            key = child.attrs.get("key")
            if not key:
                raise ValueError("<item> in <kv> requires 'key'")

            value = self._map_inline(child.children)

            items.append(
                KvItemBlock(
                    id=None,
                    key=key,
                    value=value,
                )
            )

        return KvBlock(
            type="kv",
            id=None,
            items=items,
        )

    def _map_actions(self, node: ElementNode) -> ActionBlock:
        actions: list[Action] = []

        for child in node.children:
            if is_whitespace(child):
                continue

            if not is_element(child, "action"):
                raise ValueError("<actions> can only contain <action>")

            assert isinstance(child, ElementNode)
            actions.append(self._map_action(child))

        return ActionBlock(
            type="actions",
            id=None,
            actions=actions,
        )

    def _map_action(self, node: ElementNode) -> Action:

        command = node.attrs.get("command")
        if not command:
            raise ValueError("<action> requires 'command' attribute")

        label = extract_text(node).strip()
        if not label:
            raise ValueError("<action> requires label text")

        scope = node.attrs.get("scope")

        return Action(
            label=label,
            scope=scope,
            command=command,
        )

    def _map_fields(self, node: ElementNode) -> FieldsBlock:
        fields: list[Field] = []
        for child in node.children:
            if is_whitespace(child):
                continue

            if not is_element(child, "field"):
                raise ValueError("<fields> can only contain <field>")

            assert isinstance(child, ElementNode)
            fields.append(self._map_field(child))

        name = node.attrs.get("name")
        return FieldsBlock(
            type="fields",
            name=name,
            id=None,
            fields=fields,
        )

    def _map_field(self, node: ElementNode) -> Field:
        policy = node.attrs.get("policy")
        if not policy:
            raise ValueError("<field> requires 'policy'")

        name = node.attrs.get("name")
        required = node.attrs.get("required", "false").lower() == "true"
        title = node.attrs.get("title")
        lookup = node.attrs.get("lookup")
        hint = node.attrs.get("hint")
        default = node.attrs.get("default")

        return Field(
            policy=policy,
            name=name,
            required=required,
            title=title,
            lookup=lookup,
            hint=hint,
            default=default,
        )

    # --------------
    # MAP INLINES
    # --------------

    def _map_inline(self, nodes: list[Node]) -> list[Inline]:
        result: list[Inline] = []

        for node in nodes:

            # TEXT
            if isinstance(node, TextNode):
                text = normalize_text(node.text)
                if text:
                    result.append(InlineText(text=text))
                continue

            # ELEMENT
            assert isinstance(node, ElementNode)

            mapper = self._inline_mappers.get(node.tag)
            if not mapper:
                raise ValueError(f"Unknown inline tag: {node.tag}")

            result.append(mapper(node))

        return result

    def _map_inline_code(self, node: ElementNode) -> InlineCode:
        text = extract_text(node)
        return InlineCode(text=text)

    def _map_inline_cmd(self, node: ElementNode) -> InlineCmd:
        command = node.attrs.get("command")
        if not command:
            raise ValueError("<cmd> requires 'command'")

        label = extract_text(node).strip()
        if not label:
            raise ValueError("<cmd> requires label text")

        return InlineCmd(
            command=command,
            text=label,
        )

    def _map_inline_select(self, node: ElementNode) -> InlineSelect:
        value = node.attrs.get("value")
        if not value:
            raise ValueError("<select> requires 'value'")

        label = extract_text(node).strip()
        if not label:
            raise ValueError("<select> requires label text")

        return InlineSelect(
            value=value,
            text=label,
        )

    def _map_inline_link(self, node: ElementNode) -> InlineLink:
        href = node.attrs.get("href")
        if not href:
            raise ValueError("<link> requires href")

        text = extract_text(node)

        return InlineLink(
            text=text,
            href=href,
        )


# --------------
# Utilities
# --------------


def is_element(node: Node, tag: str) -> bool:
    return isinstance(node, ElementNode) and node.tag == tag


def is_whitespace(node: Node) -> bool:
    return isinstance(node, TextNode) and not node.text.strip()


def normalize_text(text: str) -> str:
    return text.lstrip("\n").rstrip()


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
